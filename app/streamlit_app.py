"""
Telecom Agent - Streamlit UI
Project 2: AI Agent replacing human operators in a telecom call center
"""

import streamlit as st
import time
from agent import run_agent, check_lm_studio_health, load_functions

# ──────────────────────────────────────────────
# Page Config
# ──────────────────────────────────────────────

st.set_page_config(
    page_title="Telecom AI Agent",
    page_icon="📞",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ──────────────────────────────────────────────
# Custom CSS
# ──────────────────────────────────────────────

st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
        padding: 1.5rem;
        border-radius: 12px;
        text-align: center;
        margin-bottom: 1.5rem;
        color: white;
    }
    .function-card {
        background: #1e293b;
        border: 1px solid #334155;
        border-radius: 10px;
        padding: 1rem;
        margin: 0.5rem 0;
    }
    .confidence-high { color: #22c55e; font-weight: bold; }
    .confidence-med  { color: #f59e0b; font-weight: bold; }
    .confidence-low  { color: #ef4444; font-weight: bold; }
    .status-online  { color: #22c55e; }
    .status-offline { color: #ef4444; }
    .chat-user      { background: #1e40af; border-radius: 12px 12px 4px 12px; padding: 0.75rem 1rem; margin: 0.5rem 0; }
    .chat-agent     { background: #1e293b; border: 1px solid #334155; border-radius: 12px 12px 12px 4px; padding: 0.75rem 1rem; margin: 0.5rem 0; }
</style>
""", unsafe_allow_html=True)

# ──────────────────────────────────────────────
# Session State Init
# ──────────────────────────────────────────────

if "messages" not in st.session_state:
    st.session_state.messages = []

if "lm_status" not in st.session_state:
    st.session_state.lm_status = None

if "last_function" not in st.session_state:
    st.session_state.last_function = None

# ──────────────────────────────────────────────
# Sidebar
# ──────────────────────────────────────────────

with st.sidebar:
    st.markdown("## ⚙️ Settings")

    # LM Studio Status
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown("**LM Studio**")
    with col2:
        if st.button("🔄", help="Check connection"):
            st.session_state.lm_status = check_lm_studio_health()

    if st.session_state.lm_status is None:
        st.session_state.lm_status = check_lm_studio_health()

    if st.session_state.lm_status:
        st.markdown('<span class="status-online">● Connected</span>', unsafe_allow_html=True)
    else:
        st.markdown('<span class="status-offline">● Disconnected</span>', unsafe_allow_html=True)
        st.warning("Start LM Studio and load Qwen2.5-3B model, then enable the local server.")

    st.divider()

    # Function Registry Stats
    st.markdown("## 📊 Registry Stats")
    try:
        functions = load_functions()
        categories = {}
        for fn in functions:
            cat = fn["category"]
            categories[cat] = categories.get(cat, 0) + 1

        st.metric("Total Functions", len(functions))
        st.metric("Categories", len(categories))

        with st.expander("Categories breakdown"):
            for cat, count in sorted(categories.items()):
                st.text(f"{cat}: {count}")
    except Exception:
        st.error("Could not load registry.")

    st.divider()

    # Last selected function details
    if st.session_state.last_function:
        fn = st.session_state.last_function
        st.markdown("## 🎯 Last Matched Function")
        st.markdown(f"**{fn['name']}**")
        st.markdown(f"*{fn['category']}*")
        st.markdown(f"🕐 {fn['estimated_time']}")
        verify_icon = "✅" if fn["requires_verification"] else "⬜"
        st.markdown(f"{verify_icon} Verification required")

        with st.expander("Steps"):
            for i, step in enumerate(fn["steps"], 1):
                st.markdown(f"{i}. {step}")

    st.divider()
    if st.button("🗑️ Clear Conversation", use_container_width=True):
        st.session_state.messages = []
        st.session_state.last_function = None
        st.rerun()

# ──────────────────────────────────────────────
# Main Header
# ──────────────────────────────────────────────

st.markdown("""
<div class="main-header">
    <h1>📞 Telecom AI Agent</h1>
    <p style="opacity:0.8; margin:0">
        AI-powered call center — replacing human operators with intelligent agents
    </p>
    <p style="font-size:0.8rem; opacity:0.6; margin-top:0.3rem">
        Data Mining Project 2 | Powered by Qwen2.5-3B via LM Studio
    </p>
</div>
""", unsafe_allow_html=True)

# ──────────────────────────────────────────────
# Quick Action Buttons
# ──────────────────────────────────────────────

st.markdown("#### 💡 Quick Examples")
cols = st.columns(4)
examples = [
    ("🔑 PIN Recovery", "I forgot my SIM PIN code, how can I recover it?"),
    ("📶 No Signal", "I have no network signal since this morning"),
    ("💰 Check Balance", "What is my current account balance?"),
    ("📱 Data Usage", "How much internet data have I used this month?"),
    ("🔒 Block Number", "I want to block a spam caller from reaching me"),
    ("🌍 Roaming", "I'm traveling abroad and need to activate roaming"),
    ("📋 View Bill", "Can you show me my last bill?"),
    ("🚨 Report Fraud", "Someone made unauthorized calls from my number"),
]

for i, col in enumerate(cols):
    with col:
        label, text = examples[i * 2]
        if st.button(label, use_container_width=True, key=f"ex_{i}_a"):
            st.session_state["_prefill"] = text
        label2, text2 = examples[i * 2 + 1]
        if st.button(label2, use_container_width=True, key=f"ex_{i}_b"):
            st.session_state["_prefill"] = text2

# ──────────────────────────────────────────────
# Chat Display
# ──────────────────────────────────────────────

st.markdown("---")
st.markdown("### 💬 Conversation")

chat_container = st.container()
with chat_container:
    if not st.session_state.messages:
        st.info("👋 Welcome! Describe your issue or select a quick example above. I can help with any telecom service.")
    else:
        for msg in st.session_state.messages:
            if msg["role"] == "user":
                st.markdown(
                    f'<div class="chat-user">👤 <strong>Customer:</strong><br>{msg["content"]}</div>',
                    unsafe_allow_html=True,
                )
            elif msg["role"] == "assistant":
                # Show function tag if available
                fn_tag = ""
                if msg.get("function_name"):
                    conf = msg.get("confidence", 0)
                    conf_class = (
                        "confidence-high" if conf >= 0.75
                        else "confidence-med" if conf >= 0.5
                        else "confidence-low"
                    )
                    conf_pct = int(conf * 100)
                    fn_tag = (
                        f'<div style="font-size:0.75rem; opacity:0.7; margin-bottom:0.4rem">'
                        f'🎯 Function: <em>{msg["function_name"]}</em> | '
                        f'<span class="{conf_class}">{conf_pct}% confidence</span>'
                        f'</div>'
                    )
                st.markdown(
                    f'<div class="chat-agent">{fn_tag}🤖 <strong>Agent:</strong><br>{msg["content"]}</div>',
                    unsafe_allow_html=True,
                )

# ──────────────────────────────────────────────
# Input
# ──────────────────────────────────────────────

prefill_value = st.session_state.pop("_prefill", "")

with st.form("chat_form", clear_on_submit=True):
    user_input = st.text_area(
        "Your request:",
        value=prefill_value,
        placeholder="Describe your issue in English or Farsi...",
        height=80,
        label_visibility="collapsed",
    )
    submitted = st.form_submit_button("📤 Send", use_container_width=True)

# ──────────────────────────────────────────────
# Agent Processing
# ──────────────────────────────────────────────

if submitted and user_input.strip():
    # Check LM Studio connection
    if not check_lm_studio_health():
        st.error("❌ LM Studio is not running. Please start LM Studio, load the Qwen2.5-3B model, and enable the local server on port 1234.")
        st.stop()

    # Add user message
    st.session_state.messages.append({"role": "user", "content": user_input.strip()})

    # Build conversation history for context (exclude function metadata)
    history = [
        {"role": m["role"], "content": m["content"]}
        for m in st.session_state.messages[:-1]  # exclude the message we just added
        if m["role"] in ("user", "assistant")
    ]

    # Run agent with progress
    with st.spinner("🤖 Agent is processing your request..."):
        try:
            start_time = time.time()
            result = run_agent(user_input.strip(), history)
            elapsed = time.time() - start_time

            # Store response
            st.session_state.messages.append({
                "role": "assistant",
                "content": result["response"],
                "function_name": result["selected_function"]["name"],
                "function_id": result["selected_function"]["id"],
                "confidence": result["confidence"],
            })
            st.session_state.last_function = result["selected_function"]

            # Show quick stats
            conf = result["confidence"]
            fn_name = result["selected_function"]["name"]
            fn_category = result["selected_function"]["category"]
            st.success(
                f"✅ Matched: **{fn_name}** ({fn_category}) | "
                f"Confidence: **{int(conf*100)}%** | "
                f"Time: {elapsed:.1f}s"
            )

        except ConnectionError as e:
            st.error(f"🔌 Connection Error: {e}")
        except TimeoutError as e:
            st.error(f"⏰ Timeout: {e}")
        except Exception as e:
            st.error(f"❌ Error: {e}")

    st.rerun()
