# 📞 Telecom AI Agent — Project 2

**Data Mining Course | AI-Powered Call Center Agent**

This project replaces human telecom operators with an AI agent. The agent understands customer requests (in English or Farsi), selects the best matching functionality from a registry of 70+ telecom functions, and guides the customer through the process — all powered by a local LLM via LM Studio.

---

## 🎯 How It Works

```
Customer Request
      │
      ▼
LLM (Qwen2.5-3B)  ──►  Reads all 70+ functions  ──►  Selects best match
      │
      ▼
Agent Response  ──►  Walks customer through steps
      │
      ▼
Streamlit Chat UI
```

**Two LLM calls per turn:**
1. **Function Selection** — The model reads all available functions and returns the best `function_id` as JSON
2. **Response Generation** — The model generates a natural, professional response using the selected function's steps

---

## 🗂️ Project Structure

```
telecom-agent/
├── app/
│   ├── agent.py          # Core agent logic (LM Studio client + pipeline)
│   └── streamlit_app.py  # Streamlit UI
├── data/
│   └── functions_registry.json  # 70+ telecom functionalities
├── requirements.txt
├── .env.example
└── README.md
```

---

## ⚙️ Setup

### 1. Prerequisites

- Python 3.10+
- [LM Studio](https://lmstudio.ai/) installed
- Model downloaded: `Qwen2.5 3B Instruct GGUF Q4_K_M`

### 2. Start LM Studio

1. Open LM Studio
2. Load the **Qwen2.5-3B-Instruct-GGUF** model
3. Go to **Local Server** tab (left sidebar)
4. Click **Start Server** (default port: 1234)
5. Confirm it shows: `Server running at http://localhost:1234`

### 3. Install & Run

```bash
# Clone the repository
git clone https://github.com/<your-username>/telecom-agent.git
cd telecom-agent

# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate        # Linux/Mac
# venv\Scripts\activate         # Windows

# Install dependencies
pip install -r requirements.txt

# Run the app
streamlit run app/streamlit_app.py
```

The app will open at **http://localhost:8501**

---

## 🧪 Example Queries

| Customer Request | Expected Function |
|---|---|
| "I forgot my SIM PIN" | `retrieve_sim_pin` |
| "I have no network signal" | `network_troubleshoot` |
| "How much data have I used?" | `check_data_usage` |
| "پین سیم کارتم را فراموش کردم" | `retrieve_sim_pin` |
| "میخوام شماره ناشناس را مسدود کنم" | `block_number` |
| "I need to activate roaming for my trip" | `roaming_activation` |
| "Someone is using my account without permission" | `fraud_report` |

---

## 📊 Function Registry

The `data/functions_registry.json` contains **70+ functions** across these categories:

| Category | Count |
|---|---|
| SIM Card | 5 |
| Account & Balance | 4 |
| Plans & Packages | 8 |
| Data & Internet | 5 |
| Billing & Invoices | 5 |
| Number Management | 5 |
| Call Services | 6 |
| SMS Services | 2 |
| Account Management | 7 |
| Technical Support | 5 |
| Security | 3 |
| Business Services | 2 |
| Complaints & Feedback | 2 |
| Value Added Services | 3 |
| Notifications | 2 |
| Store & Location | 2 |
| Network | 2 |
| Loyalty & Promotions | 3 |

---

## 🔧 Configuration

Copy `.env.example` to `.env` and adjust if needed:

```env
LM_STUDIO_URL=http://localhost:1234/v1
LM_STUDIO_MODEL=qwen2.5-3b-instruct
```

---

## 📝 Notes

- The model is small (3B) — it works well for function selection but complex multi-turn reasoning may vary
- Responses are in the same language as the customer's request (Farsi or English)
- The sidebar shows real-time matched function details and confidence score
- Conversation history (last 6 turns) is sent with each request for context

---

## 🏗️ Tech Stack

| Tool | Purpose |
|---|---|
| Python | Core language |
| Streamlit | Web UI |
| LM Studio | Local LLM server |
| Qwen2.5-3B | Language model |
| requests | HTTP client |
| JSON | Function registry |
