"""
LangChain/LangGraph Agent — Telecom Call Center
Compatible with: langchain >= 1.0, langgraph >= 1.0
Each tool calls a real FastAPI endpoint.
LLM: Qwen2.5-3B via LM Studio (OpenAI-compatible)
"""

import os
import json
import requests
from typing import Optional

from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

# ──────────────────────────────────────────────
# Config
# ──────────────────────────────────────────────

API_BASE = os.getenv("API_BASE_URL",    "http://localhost:8000")
LM_BASE  = os.getenv("LM_STUDIO_URL",  "http://localhost:1234/v1")
LM_MODEL = os.getenv("LM_STUDIO_MODEL","qwen2.5-3b-instruct")

SYSTEM_PROMPT = """You are a professional telecom call-center AI agent.
Help customers with telecom services by using the available tools to call the backend system.

RULES:
1. Always be polite and professional.
2. Use tools to get REAL data — never make up information.
3. If you need phone number or other info, ask the customer first.
4. For PUK retrieval, you MUST ask for national ID first.
5. For sensitive actions (block SIM, change plan), confirm with customer first.
6. Respond in the same language the customer uses (Farsi or English).
7. After using a tool, explain the result in simple friendly language."""


# ──────────────────────────────────────────────
# HTTP Helpers
# ──────────────────────────────────────────────

def _get(path: str, params: dict = None) -> dict:
    r = requests.get(f"{API_BASE}{path}", params=params, timeout=15)
    return r.json()

def _post(path: str, body: dict = None) -> dict:
    r = requests.post(f"{API_BASE}{path}", json=body or {}, timeout=15)
    return r.json()


# ──────────────────────────────────────────────
# Tools
# ──────────────────────────────────────────────

@tool
def get_account_info(phone: str) -> str:
    """
    Get full account information for a customer.
    Includes: plan, balance, SIM status, data usage.
    Input: phone number e.g. 09121234567
    """
    result = _get(f"/account/{phone}/info")
    return json.dumps(result, ensure_ascii=False, indent=2)


@tool
def check_balance(phone: str) -> str:
    """
    Check current account balance and active plan.
    Input: phone number e.g. 09121234567
    """
    result = _get(f"/balance/{phone}")
    return json.dumps(result, ensure_ascii=False)


@tool
def recharge_account(phone: str, amount: int) -> str:
    """
    Recharge (top-up) a customer account balance.
    Input: phone number and amount in Rials.
    Example: phone=09121234567, amount=50000
    """
    result = _post("/balance/recharge", {"phone": phone, "amount": amount})
    return json.dumps(result, ensure_ascii=False)


@tool
def check_data_usage(phone: str) -> str:
    """
    Check internet data usage — how much used and how much remains.
    Input: phone number e.g. 09121234567
    """
    result = _get(f"/data/{phone}/usage")
    return json.dumps(result, ensure_ascii=False)


@tool
def get_sim_info(phone: str) -> str:
    """
    Get SIM card information: status (active/blocked), network type, ICCID.
    Input: phone number e.g. 09121234567
    """
    result = _get(f"/sim/{phone}")
    return json.dumps(result, ensure_ascii=False)


@tool
def retrieve_puk_code(phone: str, national_id: str) -> str:
    """
    Retrieve PUK code to unblock a blocked/PIN-locked SIM card.
    Requires identity verification via national ID.
    Input: phone number and national_id (10 digits)
    Example: phone=09011234567, national_id=1122334455
    """
    result = _post("/sim/puk", {"phone": phone, "national_id": national_id})
    return json.dumps(result, ensure_ascii=False)


@tool
def block_sim_card(phone: str) -> str:
    """
    Block (suspend) a SIM card immediately.
    Use when customer reports lost or stolen phone.
    Input: phone number e.g. 09121234567
    """
    result = _post(f"/sim/{phone}/block")
    return json.dumps(result, ensure_ascii=False)


@tool
def unblock_sim_card(phone: str) -> str:
    """
    Unblock a previously blocked SIM card.
    Input: phone number e.g. 09121234567
    """
    result = _post(f"/sim/{phone}/unblock")
    return json.dumps(result, ensure_ascii=False)


@tool
def get_available_plans() -> str:
    """
    Get all available subscription plans with prices and features.
    No input needed.
    """
    result = _get("/plans")
    return json.dumps(result, ensure_ascii=False, indent=2)


@tool
def change_subscription_plan(phone: str, new_plan: str) -> str:
    """
    Change a customer's subscription plan.
    Input: phone number and plan name.
    Available plans: Basic, Silver, Gold, Platinum
    Example: phone=09351234567, new_plan=Gold
    """
    result = _post("/plans/change", {"phone": phone, "new_plan": new_plan})
    return json.dumps(result, ensure_ascii=False)


@tool
def block_phone_number(customer_phone: str, number_to_block: str) -> str:
    """
    Block a specific phone number from calling/texting the customer (anti-spam).
    Input: customer's phone and the number they want to block.
    Example: customer_phone=09121234567, number_to_block=09999999999
    """
    result = _post("/calls/block-number", {
        "phone": customer_phone,
        "block_number": number_to_block
    })
    return json.dumps(result, ensure_ascii=False)


@tool
def get_blocklist(phone: str) -> str:
    """
    Get the list of phone numbers blocked by this customer.
    Input: phone number e.g. 09121234567
    """
    result = _get(f"/calls/blocklist/{phone}")
    return json.dumps(result, ensure_ascii=False)


@tool
def get_order_status(order_id: str) -> str:
    """
    Check the status of an order: pending, shipped, or delivered.
    Input: order ID e.g. ord001, ord002
    """
    result = _get(f"/orders/{order_id}/status")
    return json.dumps(result, ensure_ascii=False)


@tool
def get_user_orders(phone: str) -> str:
    """
    Get all orders history for a customer.
    Input: phone number e.g. 09121234567
    """
    info = _get(f"/account/{phone}/info")
    if "user" not in info:
        return f"User not found for phone {phone}"
    user_id = info["user"]["id"]
    result = _get(f"/users/{user_id}/orders")
    return json.dumps(result, ensure_ascii=False, indent=2)


@tool
def submit_complaint(phone: str, subject: str, description: str) -> str:
    """
    Submit a formal complaint or support ticket.
    Input: customer phone, complaint subject, and description.
    Example: phone=09121234567, subject=Billing Issue, description=I was charged twice
    """
    result = _post("/complaints", {
        "phone": phone,
        "subject": subject,
        "description": description
    })
    return json.dumps(result, ensure_ascii=False)


@tool
def track_complaint(ticket_id: str) -> str:
    """
    Track the status of an existing complaint ticket.
    Input: ticket ID e.g. TKT-AB12CD34
    """
    result = _get(f"/complaints/{ticket_id}")
    return json.dumps(result, ensure_ascii=False)


@tool
def suspend_account(phone: str) -> str:
    """
    Temporarily suspend a customer's account.
    Input: phone number e.g. 09121234567
    """
    result = _post(f"/account/{phone}/suspend")
    return json.dumps(result, ensure_ascii=False)


@tool
def reactivate_account(phone: str) -> str:
    """
    Reactivate a previously suspended account.
    Input: phone number e.g. 09121234567
    """
    result = _post(f"/account/{phone}/reactivate")
    return json.dumps(result, ensure_ascii=False)


# ──────────────────────────────────────────────
# All tools list
# ──────────────────────────────────────────────

ALL_TOOLS = [
    get_account_info,
    check_balance,
    recharge_account,
    check_data_usage,
    get_sim_info,
    retrieve_puk_code,
    block_sim_card,
    unblock_sim_card,
    get_available_plans,
    change_subscription_plan,
    block_phone_number,
    get_blocklist,
    get_order_status,
    get_user_orders,
    submit_complaint,
    track_complaint,
    suspend_account,
    reactivate_account,
]


# ──────────────────────────────────────────────
# Build Agent
# ──────────────────────────────────────────────

def build_agent():
    """
    Build and return a LangGraph ReAct agent with memory.
    Compatible with langchain >= 1.0 / langgraph >= 1.0
    """
    llm = ChatOpenAI(
        base_url=LM_BASE,
        api_key="lm-studio",   # LM Studio doesn't need a real key
        model=LM_MODEL,
        temperature=0.2,
        max_tokens=1024,
    )

    memory = MemorySaver()

    agent = create_react_agent(
        model=llm,
        tools=ALL_TOOLS,
        prompt=SYSTEM_PROMPT,
        checkpointer=memory,
    )

    return agent


def run_agent(agent, message: str, thread_id: str = "default") -> dict:
    """
    Run the agent on a user message.
    Returns: { response, messages, tool_calls }
    thread_id keeps conversation memory separate per session.
    """
    config = {"configurable": {"thread_id": thread_id}}

    result = agent.invoke(
        {"messages": [HumanMessage(content=message)]},
        config=config,
    )

    all_messages = result.get("messages", [])

    # Last AI message = final response
    response_text = ""
    for msg in reversed(all_messages):
        if isinstance(msg, AIMessage) and msg.content:
            response_text = msg.content
            break

    # Extract tool calls from all messages
    tool_calls_used = []
    for msg in all_messages:
        if hasattr(msg, "tool_calls") and msg.tool_calls:
            for tc in msg.tool_calls:
                tool_calls_used.append(tc.get("name", "unknown"))

    return {
        "response":   response_text,
        "messages":   all_messages,
        "tool_calls": tool_calls_used,
    }


# ──────────────────────────────────────────────
# Health Checks
# ──────────────────────────────────────────────

def check_api_health() -> bool:
    """Check if FastAPI backend is running."""
    try:
        r = requests.get(f"{API_BASE}/health", timeout=3)
        return r.status_code == 200
    except Exception:
        return False


def check_lm_health() -> bool:
    """Check if LM Studio server is running."""
    try:
        r = requests.get(f"{LM_BASE}/models", timeout=3)
        return r.status_code == 200
    except Exception:
        return False