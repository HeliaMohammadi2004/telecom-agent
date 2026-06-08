"""
Telecom Agent - Core Logic
Handles function matching, LM Studio API calls, and agent execution
"""

import json
import os
import requests
from typing import Optional


# ──────────────────────────────────────────────
# Configuration
# ──────────────────────────────────────────────

LM_STUDIO_BASE_URL = os.getenv("LM_STUDIO_URL", "http://localhost:1234/v1")
MODEL_NAME = os.getenv("LM_STUDIO_MODEL", "qwen2.5-3b-instruct")


# ──────────────────────────────────────────────
# Function Registry
# ──────────────────────────────────────────────

def load_functions() -> list[dict]:
    """Load all telecom functionalities from the JSON registry."""
    registry_path = os.path.join(os.path.dirname(__file__), "..", "data", "functions_registry.json")
    with open(registry_path, "r", encoding="utf-8") as f:
        return json.load(f)


def get_functions_summary(functions: list[dict]) -> str:
    """Build a compact text summary of all functions for the prompt."""
    lines = []
    for fn in functions:
        keywords = ", ".join(fn["keywords"][:4])
        lines.append(
            f"- ID: {fn['id']} | Name: {fn['name']} | Category: {fn['category']}\n"
            f"  Description: {fn['description']}\n"
            f"  Keywords: {keywords}"
        )
    return "\n".join(lines)


# ──────────────────────────────────────────────
# LM Studio API Client
# ──────────────────────────────────────────────

def call_lm_studio(messages: list[dict], temperature: float = 0.3, max_tokens: int = 1024) -> str:
    """Send a request to LM Studio's OpenAI-compatible API."""
    url = f"{LM_STUDIO_BASE_URL}/chat/completions"
    payload = {
        "model": MODEL_NAME,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    try:
        response = requests.post(url, json=payload, timeout=60)
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"].strip()
    except requests.exceptions.ConnectionError:
        raise ConnectionError(
            "Cannot connect to LM Studio. Make sure LM Studio is running "
            f"with the server on {LM_STUDIO_BASE_URL}"
        )
    except requests.exceptions.Timeout:
        raise TimeoutError("LM Studio request timed out. Try a simpler query.")
    except Exception as e:
        raise RuntimeError(f"LM Studio API error: {e}")


def check_lm_studio_health() -> bool:
    """Check if LM Studio server is reachable."""
    try:
        response = requests.get(f"{LM_STUDIO_BASE_URL}/models", timeout=5)
        return response.status_code == 200
    except Exception:
        return False


# ──────────────────────────────────────────────
# Agent: Select Best Function
# ──────────────────────────────────────────────

SELECTION_SYSTEM_PROMPT = """You are a telecom call-center routing agent.
Your job is to read a customer's request and select the most appropriate function from the provided list.

RULES:
1. Read the customer request carefully.
2. From the function list, pick the ONE best matching function.
3. Respond ONLY with a valid JSON object in this exact format:
   {"function_id": "...", "confidence": 0.95, "reasoning": "brief reason"}
4. Do NOT include any explanation or text outside the JSON.
5. If no function matches well, use the closest one and set confidence below 0.5."""


def select_function(customer_request: str, functions: list[dict]) -> dict:
    """
    Use LLM to select the best matching function for the customer's request.
    Returns the matched function dict with reasoning.
    """
    functions_text = get_functions_summary(functions)

    messages = [
        {"role": "system", "content": SELECTION_SYSTEM_PROMPT},
        {
            "role": "user",
            "content": (
                f"Customer request: {customer_request}\n\n"
                f"Available functions:\n{functions_text}\n\n"
                f"Select the best matching function ID."
            ),
        },
    ]

    raw_response = call_lm_studio(messages, temperature=0.1, max_tokens=200)

    # Parse JSON response
    try:
        # Handle cases where model might wrap in code blocks
        clean = raw_response.strip()
        if "```" in clean:
            clean = clean.split("```")[1]
            if clean.startswith("json"):
                clean = clean[4:]
        result = json.loads(clean)
    except json.JSONDecodeError:
        # Fallback: try to extract JSON substring
        import re
        match = re.search(r'\{.*?\}', raw_response, re.DOTALL)
        if match:
            result = json.loads(match.group())
        else:
            raise ValueError(f"Could not parse LLM selection response: {raw_response}")

    # Find the actual function object
    selected_fn = next((f for f in functions if f["id"] == result.get("function_id")), None)
    if not selected_fn:
        # Fallback: take first function that shares category hint
        selected_fn = functions[0]

    return {
        "function": selected_fn,
        "confidence": result.get("confidence", 0.5),
        "reasoning": result.get("reasoning", ""),
    }


# ──────────────────────────────────────────────
# Agent: Generate Response
# ──────────────────────────────────────────────

RESPONSE_SYSTEM_PROMPT = """You are a professional telecom call-center agent.
You help customers by executing the appropriate service function.
Be concise, friendly, and professional.
Respond in the same language the customer used (Farsi or English).
Structure your response as:
1. Acknowledge the customer's request
2. Explain what you are doing (the selected function)
3. Walk through the steps clearly
4. Ask for any needed information
Keep the response under 200 words."""


def generate_agent_response(
    customer_request: str,
    selected_function: dict,
    conversation_history: list[dict],
) -> str:
    """
    Generate the agent's actual response to the customer using the selected function.
    """
    fn = selected_function["function"]
    steps_text = "\n".join(f"  {i+1}. {s}" for i, s in enumerate(fn["steps"]))
    requires_verify = "Yes - must verify customer identity" if fn["requires_verification"] else "No"

    function_context = (
        f"Selected Function: {fn['name']} ({fn['id']})\n"
        f"Category: {fn['category']}\n"
        f"Description: {fn['description']}\n"
        f"Steps to follow:\n{steps_text}\n"
        f"Estimated time: {fn['estimated_time']}\n"
        f"Requires verification: {requires_verify}"
    )

    # Build messages with history
    messages = [{"role": "system", "content": RESPONSE_SYSTEM_PROMPT}]

    # Add conversation history (last 6 turns to stay within context)
    for turn in conversation_history[-6:]:
        messages.append(turn)

    messages.append({
        "role": "user",
        "content": (
            f"Customer request: {customer_request}\n\n"
            f"[FUNCTION CONTEXT - do not reveal these details to customer directly]\n"
            f"{function_context}\n\n"
            f"Now respond to the customer professionally."
        ),
    })

    return call_lm_studio(messages, temperature=0.5, max_tokens=512)


# ──────────────────────────────────────────────
# Main Agent Entry Point
# ──────────────────────────────────────────────

def run_agent(
    customer_request: str,
    conversation_history: Optional[list[dict]] = None,
) -> dict:
    """
    Main agent pipeline:
    1. Load functions
    2. Select best matching function
    3. Generate professional response

    Returns:
        {
            "response": str,
            "selected_function": dict,
            "confidence": float,
            "reasoning": str,
        }
    """
    if conversation_history is None:
        conversation_history = []

    functions = load_functions()
    selection_result = select_function(customer_request, functions)
    response = generate_agent_response(
        customer_request, selection_result, conversation_history
    )

    return {
        "response": response,
        "selected_function": selection_result["function"],
        "confidence": selection_result["confidence"],
        "reasoning": selection_result["reasoning"],
    }
