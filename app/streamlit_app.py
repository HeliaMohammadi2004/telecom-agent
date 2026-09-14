import sys
import os
import time
import uuid
import streamlit as st
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "agent"))
from langchain_agent import build_agent, run_agent, check_api_health, check_lm_health, ALL_TOOLS

st.set_page_config(
    page_title="Telecom AI Agent",
    page_icon="📞",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&family=IBM+Plex+Sans:wght@300;400;600&display=swap');

html, body, [class*="css"] { font-family: 'IBM Plex Sans', sans-serif; }

.header-box {
    background: linear-gradient(135deg, #0a0a0f 0%, #0d1b2a 50%, #0a1628 100%);
    border: 1px solid #1e3a5f;
    border-radius: 16px;
    padding: 2rem;
    text-align: center;
    margin-bottom: 1.5rem;
}
.header-box h1 { color: #e2e8f0; font-size: 2rem; margin: 0; letter-spacing: -0.5px; }
.header-box p  { color: #64748b; margin: 0.4rem 0 0; font-size: 0.9rem; }
.header-accent { color: #38bdf8; font-family: 'IBM Plex Mono', monospace; }

.status-pill {
    display: inline-block;
    padding: 0.3rem 0.9rem;
    border-radius: 20px;
    font-size: 0.78rem;
    font-family: 'IBM Plex Mono', monospace;
    font-weight: 600;
    margin-bottom: 0.4rem;
}
.pill-ok   { background:#052e16; color:#4ade80; border:1px solid #166534; }
.pill-err  { background:#2d0a0a; color:#f87171; border:1px solid #7f1d1d; }

.msg-user {
    background: #1e3a5f;
    border-radius: 16px 16px 4px 16px;
    padding: 0.85rem 1.1rem;
    margin: 0.6rem 0;
    color: #e2e8f0;
    border-left: 3px solid #38bdf8;
}
.msg-agent {
    background: #0f172a;
    border: 1px solid #1e293b;
    border-radius: 16px 16px 16px 4px;
    padding: 0.85rem 1.1rem;
    margin: 0.6rem 0;
    color: #cbd5e1;
    border-left: 3px solid #22d3ee;
}
.msg-label {
    font-size: 0.72rem;
    font-family: 'IBM Plex Mono', monospace;
    opacity: 0.5;
    margin-bottom: 0.35rem;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}
.tool-badge {
    display: inline-block;
    background: #0c2340;
    color: #7dd3fc;
    border: 1px solid #1e4a7a;
    border-radius: 6px;
    padding: 0.15rem 0.5rem;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.72rem;
    margin: 0.1rem 0.1rem 0.3rem 0;
}
.sidebar-box {
    background: #0a0f1a;
    border: 1px solid #1e293b;
    border-radius: 10px;
    padding: 0.8rem;
    margin-bottom: 0.8rem;
}
.sidebar-box h4 {
    color: #64748b;
    font-size: 0.72rem;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    margin: 0 0 0.6rem;
}
</style>
""", unsafe_allow_html=True)


if "messages"   not in st.session_state: st.session_state.messages   = []
if "agent"      not in st.session_state: st.session_state.agent      = None
if "api_ok"     not in st.session_state: st.session_state.api_ok     = False
if "lm_ok"      not in st.session_state: st.session_state.lm_ok      = False
if "last_tools" not in st.session_state: st.session_state.last_tools = []
if "thread_id"  not in st.session_state: st.session_state.thread_id  = str(uuid.uuid4())


def refresh_status():
    st.session_state.api_ok = check_api_health()
    st.session_state.lm_ok  = check_lm_health()
    if st.session_state.api_ok and st.session_state.lm_ok:
        try:
            st.session_state.agent = build_agent()
        except Exception:
            st.session_state.agent = None


if st.session_state.agent is None:
    refresh_status()

with st.sidebar:
    st.markdown("## ⚙️ System Status")

    api_cls  = "pill-ok"  if st.session_state.api_ok else "pill-err"
    lm_cls   = "pill-ok"  if st.session_state.lm_ok  else "pill-err"
    api_txt  = "● FastAPI   ONLINE"   if st.session_state.api_ok else "● FastAPI   OFFLINE"
    lm_txt   = "● LM Studio  ONLINE"  if st.session_state.lm_ok  else "● LM Studio  OFFLINE"

    st.markdown(f"""
    <div class="sidebar-box">
        <span class="status-pill {api_cls}">{api_txt}</span><br>
        <span class="status-pill {lm_cls}">{lm_txt}</span>
    </div>""", unsafe_allow_html=True)

    if st.button("🔄 Refresh Status", use_container_width=True):
        refresh_status()
        st.rerun()

    if not st.session_state.api_ok:
        st.warning("run in terminal:\n```\nuvicorn backend.main:app --reload\n```")
    if not st.session_state.lm_ok:
        st.warning("LM Studio → Local Server → Start (port 1234)")

    st.divider()

    st.markdown("## 🔧 LangChain Tools")
    st.markdown(
        f'<div class="sidebar-box"><h4>{len(ALL_TOOLS)} tools</h4>'
        + "".join(f'<span class="tool-badge">{t.name}</span>' for t in ALL_TOOLS)
        + "</div>",
        unsafe_allow_html=True,
    )

    st.divider()

    st.markdown("## 👥 Test Users")
    st.markdown("""<div class="sidebar-box">
        <h4>Mock Database</h4>
        <span class="tool-badge">09121234567</span> Ali — Gold ✅<br><br>
        <span class="tool-badge">09351234567</span> Sara — Silver ✅<br><br>
        <span class="tool-badge">09011234567</span> Reza — Basic ⏸️
    </div>""", unsafe_allow_html=True)

    if st.session_state.last_tools:
        st.divider()
        st.markdown("## 🎯 Last API Calls")
        st.markdown(
            '<div class="sidebar-box"><h4>Tools called</h4>'
            + "".join(f'<span class="tool-badge">✓ {t}</span>' for t in st.session_state.last_tools)
            + "</div>",
            unsafe_allow_html=True,
        )

    st.divider()
    if st.button("🗑️ Clear Chat", use_container_width=True):
        st.session_state.messages   = []
        st.session_state.last_tools = []
        st.session_state.thread_id  = str(uuid.uuid4()) 
        if st.session_state.api_ok and st.session_state.lm_ok:
            st.session_state.agent = build_agent()
        st.rerun()

st.markdown("""
<div class="header-box">
    <h1>🤖 Telecom AI Agent</h1>
    <p>
        <span class="header-accent">LangGraph</span> &nbsp;·&nbsp;
        <span class="header-accent">FastAPI</span> &nbsp;·&nbsp;
        <span class="header-accent">Qwen2.5-3B</span> &nbsp;·&nbsp;
        <span class="header-accent">LM Studio</span>
    </p>
</div>
""", unsafe_allow_html=True)

st.markdown("### 💬 Conversation")

if not st.session_state.messages:
    st.markdown("""
    <div style="text-align:center;padding:2.5rem;color:#334155;">
        <div style="font-size:3rem">📞</div>
        <div style="font-size:1.1rem;margin-top:0.5rem;color:#475569">سلام! چطور می‌تونم کمکتون کنم؟</div>
        <div style="font-size:0.85rem;color:#1e3a5f;margin-top:0.3rem">Hello! How can I help you today?</div>
    </div>""", unsafe_allow_html=True)

for msg in st.session_state.messages:
    if msg["role"] == "user":
        st.markdown(
            f'<div class="msg-user"><div class="msg-label">👤 Customer</div>{msg["content"]}</div>',
            unsafe_allow_html=True,
        )
    else:
        tools_html = ""
        if msg.get("tool_calls"):
            tools_html = (
                "<div style='margin-bottom:0.4rem'>"
                + "".join(f'<span class="tool-badge">⚡ {t}</span>' for t in msg["tool_calls"])
                + "</div>"
            )
        elapsed_html = f'<div style="font-size:0.7rem;color:#334155;margin-top:0.4rem">⏱ {msg.get("elapsed","?")}s</div>'
        st.markdown(
            f'<div class="msg-agent">'
            f'<div class="msg-label">🤖 AI Agent</div>'
            f'{tools_html}{msg["content"]}{elapsed_html}'
            f'</div>',
            unsafe_allow_html=True,
        )

prefill = st.session_state.pop("_prefill", "")

with st.form("chat_form", clear_on_submit=True):
    user_input = st.text_area(
        "message",
        value=prefill,
        placeholder="Send a request in Persian or English...",
        height=85,
        label_visibility="collapsed",
    )
    submitted = st.form_submit_button("📤 Send", use_container_width=True)

if submitted and user_input.strip():

    if not st.session_state.api_ok:
        st.error("❌ FastAPI is not running.\n```\nuvicorn backend.main:app --reload\n```")
        st.stop()
    if not st.session_state.lm_ok:
        st.error("❌ LM Studio is not running. Start the server on port 1234.")
        st.stop()
    if st.session_state.agent is None:
        st.error("❌ Agent is not created — Refresh the page.")
        st.stop()

    st.session_state.messages.append({"role": "user", "content": user_input.strip()})

    with st.spinner("🤖 Agent is processing..."):
        try:
            t0 = time.time()
            result = run_agent(
                st.session_state.agent,
                user_input.strip(),
                thread_id=st.session_state.thread_id,
            )
            elapsed = round(time.time() - t0, 1)

            tools_used = result["tool_calls"]
            st.session_state.last_tools = tools_used

            st.session_state.messages.append({
                "role":       "assistant",
                "content":    result["response"],
                "tool_calls": tools_used,
                "elapsed":    elapsed,
            })

            if tools_used:
                st.success(f"✅ {len(tools_used)} API call(s): {' → '.join(tools_used)} | {elapsed}s")
            else:
                st.info(f"💬 Responded without API calls | {elapsed}s")

        except Exception as e:
            err = str(e)
            if "Connection" in err or "refused" in err:
                st.error("🔌 Connection to FastAPI or LM Studio was lost. Check the services.")
            else:
                st.error(f"❌ Error: {err}")

    st.rerun()