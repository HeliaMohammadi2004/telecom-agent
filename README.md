# 📞 Telecom AI Agent — Project 2

**Data Mining Course | LangChain + FastAPI + LM Studio**

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────┐
│                   Streamlit UI                      │
│              (app/streamlit_app.py)                 │
└───────────────────────┬─────────────────────────────┘
                        │  user message
                        ▼
┌─────────────────────────────────────────────────────┐
│             LangChain ReAct Agent                   │
│           (agent/langchain_agent.py)                │
│                                                     │
│  LLM: Qwen2.5-3B  ◄──────►  17 LangChain Tools    │
│  (via LM Studio)             (one per API group)   │
└───────────────────────┬─────────────────────────────┘
                        │  HTTP calls
                        ▼
┌─────────────────────────────────────────────────────┐
│              FastAPI Backend                        │
│              (backend/main.py)                      │
│                                                     │
│   /users  /balance  /sim  /data  /plans             │
│   /orders  /calls  /complaints  /account            │
└─────────────────────────────────────────────────────┘
```

**Flow per message:**
1. Customer types a request
2. LangChain ReAct agent thinks → selects tool → calls FastAPI endpoint
3. Gets real data from mock database
4. LLM formats a natural response
5. UI shows response + which tools were called

---

## 📁 Project Structure

```
telecom-agent/
├── backend/
│   └── main.py              # FastAPI — all endpoints + mock database
├── agent/
│   └── langchain_agent.py   # LangChain ReAct agent + 17 tools
├── app/
│   └── streamlit_app.py     # Streamlit chat UI
├── requirements.txt
├── .env.example
└── README.md
```

---

## ⚙️ Setup & Run

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Start LM Studio
1. Open LM Studio
2. Load **Qwen2.5-3B-Instruct-GGUF Q4_K_M**
3. Go to **Local Server** tab → **Start Server** (port 1234)

### 3. Start FastAPI backend
```bash
# From project root
uvicorn backend.main:app --reload --port 8000
```
API docs available at: **http://localhost:8000/docs**

### 4. Start Streamlit UI
```bash
# From project root
streamlit run app/streamlit_app.py
```
App available at: **http://localhost:8501**

---

## 🔧 API Endpoints

| Method | URL | Description |
|--------|-----|-------------|
| GET | `/users` | List users (page, limit) |
| GET | `/users/{id}` | Get user by ID |
| POST | `/users` | Create new user |
| GET | `/orders/{id}/status` | Get order status |
| GET | `/balance/{phone}` | Check balance |
| POST | `/balance/recharge` | Recharge account |
| GET | `/sim/{phone}` | SIM card info |
| POST | `/sim/puk` | Get PUK (requires national ID) |
| POST | `/sim/{phone}/block` | Block SIM |
| GET | `/data/{phone}/usage` | Data usage |
| GET | `/plans` | All plans |
| POST | `/plans/change` | Change plan |
| POST | `/calls/block-number` | Block a number |
| POST | `/complaints` | Submit complaint |
| GET | `/complaints/{id}` | Track complaint |
| POST | `/account/{phone}/suspend` | Suspend account |
| GET | `/account/{phone}/info` | Full account info |

---

## 🧪 Test Users (Mock Database)

| Phone | Name | Plan | Status |
|-------|------|------|--------|
| 09121234567 | Ali Rezaei | Gold | active |
| 09351234567 | Sara Mohammadi | Silver | active |
| 09011234567 | Reza Hosseini | Basic | suspended |

---

## 💬 Example Queries

| Query | Tools Called |
|-------|-------------|
| موجودی حساب 09121234567 | `check_balance` |
| مصرف اینترنت 09351234567 | `check_data_usage` |
| پین قفله، کد ملی 1122334455 | `retrieve_puk_code` |
| طرح‌های موجود | `get_available_plans` |
| ارتقا به Gold برای 09351234567 | `get_available_plans` → `change_subscription_plan` |
| بلاک کردن 09999999999 | `block_phone_number` |
| وضعیت سفارش ord002 | `get_order_status` |

---

## 🔬 LangChain ReAct Chain

The agent uses **ReAct** (Reasoning + Acting) pattern:
```
Thought: I need to check the customer's balance
Action: check_balance
Action Input: 09121234567
Observation: {"phone": "09121234567", "balance": 45000, "plan": "Gold"}
Thought: I now have the balance info
Final Answer: موجودی حساب شما 45,000 ریال است و طرح فعلی شما Gold می‌باشد.
```

---

## 🛠️ Tech Stack

| Component | Technology |
|-----------|-----------|
| LLM | Qwen2.5-3B-Instruct (local) |
| LLM Server | LM Studio |
| Agent Framework | LangChain ReAct |
| Backend API | FastAPI |
| UI | Streamlit |
| Language | Python 3.10+ |
