"""
Telecom Backend API — FastAPI
Mock database + all telecom endpoints the LangChain Agent will call
"""

from fastapi import FastAPI, HTTPException, Query, Path
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime, timedelta
import random
import uuid

app = FastAPI(title="Telecom Backend API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ──────────────────────────────────────────────
# Mock Database
# ──────────────────────────────────────────────

USERS_DB: dict[str, dict] = {
    "u001": {
        "id": "u001", "name": "Ali Rezaei", "email": "ali@example.com",
        "phone": "09121234567", "national_id": "1234567890",
        "plan": "Gold", "balance": 45000, "status": "active",
        "created_at": "2023-01-15",
    },
    "u002": {
        "id": "u002", "name": "Sara Mohammadi", "email": "sara@example.com",
        "phone": "09351234567", "national_id": "0987654321",
        "plan": "Silver", "balance": 12000, "status": "active",
        "created_at": "2023-06-20",
    },
    "u003": {
        "id": "u003", "name": "Reza Hosseini", "email": "reza@example.com",
        "phone": "09011234567", "national_id": "1122334455",
        "plan": "Basic", "balance": 3500, "status": "suspended",
        "created_at": "2022-11-10",
    },
}

SIMS_DB: dict[str, dict] = {
    "09121234567": {
        "iccid": "8998210000000001234", "phone": "09121234567",
        "user_id": "u001", "status": "active", "pin_blocked": False,
        "puk": "12345678", "network": "4G",
    },
    "09351234567": {
        "iccid": "8998210000000005678", "phone": "09351234567",
        "user_id": "u002", "status": "active", "pin_blocked": False,
        "puk": "87654321", "network": "3G",
    },
    "09011234567": {
        "iccid": "8998210000000009012", "phone": "09011234567",
        "user_id": "u003", "status": "blocked", "pin_blocked": True,
        "puk": "11223344", "network": "4G",
    },
}

DATA_USAGE_DB: dict[str, dict] = {
    "09121234567": {"total_gb": 20.0, "used_gb": 14.3, "reset_date": "2026-06-30"},
    "09351234567": {"total_gb": 10.0, "used_gb": 9.8,  "reset_date": "2026-06-25"},
    "09011234567": {"total_gb": 5.0,  "used_gb": 1.2,  "reset_date": "2026-06-28"},
}

PLANS_DB = {
    "Basic":    {"name": "Basic",    "price": 150000, "data_gb": 5,  "calls_min": 100, "sms": 50},
    "Silver":   {"name": "Silver",   "price": 300000, "data_gb": 10, "calls_min": 300, "sms": 200},
    "Gold":     {"name": "Gold",     "price": 500000, "data_gb": 20, "calls_min": 600, "sms": 500},
    "Platinum": {"name": "Platinum", "price": 900000, "data_gb": 50, "calls_min": 999, "sms": 999},
}

ORDERS_DB: dict[str, dict] = {
    "ord001": {"id": "ord001", "user_id": "u001", "item": "Gold Plan Renewal", "amount": 500000, "status": "delivered", "created_at": "2026-05-01"},
    "ord002": {"id": "ord002", "user_id": "u001", "item": "Extra 5GB Data Bundle", "amount": 80000, "status": "shipped",   "created_at": "2026-06-01"},
    "ord003": {"id": "ord003", "user_id": "u002", "item": "SIM Replacement",      "amount": 50000, "status": "pending",   "created_at": "2026-06-07"},
}

TICKETS_DB: dict[str, dict] = {}

BLOCKLIST_DB: dict[str, list] = {
    "09121234567": [],
    "09351234567": ["09999999999"],
    "09011234567": [],
}

# ──────────────────────────────────────────────
# Schemas
# ──────────────────────────────────────────────

class UserCreate(BaseModel):
    name: str
    email: str
    phone: str
    national_id: str
    password: str

class RechargeRequest(BaseModel):
    phone: str
    amount: int

class PlanChangeRequest(BaseModel):
    phone: str
    new_plan: str

class BlockNumberRequest(BaseModel):
    phone: str
    block_number: str

class ComplaintCreate(BaseModel):
    phone: str
    subject: str
    description: str

class SimPukRequest(BaseModel):
    phone: str
    national_id: str

class DataLimitRequest(BaseModel):
    phone: str
    limit_gb: float

# ──────────────────────────────────────────────
# Helper
# ──────────────────────────────────────────────

def find_user_by_phone(phone: str) -> Optional[dict]:
    for u in USERS_DB.values():
        if u["phone"] == phone:
            return u
    return None

def require_user(phone: str) -> dict:
    u = find_user_by_phone(phone)
    if not u:
        raise HTTPException(status_code=404, detail=f"No user found with phone {phone}")
    return u

# ──────────────────────────────────────────────
# ── Users ──
# ──────────────────────────────────────────────

@app.get("/users", summary="Get list of users")
def get_users(page: int = Query(1, ge=1), limit: int = Query(10, ge=1, le=100)):
    """دریافت لیست کاربران با صفحه‌بندی"""
    all_users = list(USERS_DB.values())
    start = (page - 1) * limit
    return {
        "page": page, "limit": limit,
        "total": len(all_users),
        "users": all_users[start: start + limit],
    }

@app.get("/users/{user_id}", summary="Get user by ID")
def get_user(user_id: str = Path(...)):
    """دریافت اطلاعات کامل کاربر بر اساس شناسه"""
    if user_id not in USERS_DB:
        raise HTTPException(status_code=404, detail="User not found")
    return USERS_DB[user_id]

@app.post("/users", status_code=201, summary="Create new user")
def create_user(body: UserCreate):
    """ثبت کاربر جدید — email باید یونیک باشد"""
    for u in USERS_DB.values():
        if u["email"] == body.email:
            raise HTTPException(status_code=409, detail="Email already exists")
    new_id = f"u{str(len(USERS_DB)+1).zfill(3)}"
    user = {
        "id": new_id, "name": body.name, "email": body.email,
        "phone": body.phone, "national_id": body.national_id,
        "plan": "Basic", "balance": 0, "status": "active",
        "created_at": datetime.now().strftime("%Y-%m-%d"),
    }
    USERS_DB[new_id] = user
    SIMS_DB[body.phone] = {
        "iccid": f"899821{random.randint(1000000000000,9999999999999)}",
        "phone": body.phone, "user_id": new_id,
        "status": "active", "pin_blocked": False,
        "puk": str(random.randint(10000000, 99999999)), "network": "4G",
    }
    DATA_USAGE_DB[body.phone] = {"total_gb": 5.0, "used_gb": 0.0, "reset_date": (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")}
    BLOCKLIST_DB[body.phone] = []
    return user

# ──────────────────────────────────────────────
# ── Orders ──
# ──────────────────────────────────────────────

@app.get("/orders/{order_id}/status", summary="Get order status")
def get_order_status(order_id: str = Path(...)):
    """دریافت وضعیت فعلی سفارش — فقط به سفارش‌های خودت دسترسی داری"""
    if order_id not in ORDERS_DB:
        raise HTTPException(status_code=404, detail="Order not found")
    o = ORDERS_DB[order_id]
    return {"order_id": order_id, "item": o["item"], "status": o["status"], "created_at": o["created_at"]}

@app.get("/users/{user_id}/orders", summary="Get all orders of a user")
def get_user_orders(user_id: str):
    if user_id not in USERS_DB:
        raise HTTPException(404, "User not found")
    orders = [o for o in ORDERS_DB.values() if o["user_id"] == user_id]
    return {"user_id": user_id, "orders": orders}

# ──────────────────────────────────────────────
# ── Balance & Recharge ──
# ──────────────────────────────────────────────

@app.get("/balance/{phone}", summary="Check account balance")
def check_balance(phone: str):
    """بررسی موجودی حساب"""
    user = require_user(phone)
    return {"phone": phone, "name": user["name"], "balance": user["balance"], "plan": user["plan"]}

@app.post("/balance/recharge", summary="Recharge account")
def recharge(body: RechargeRequest):
    """شارژ حساب"""
    user = require_user(body.phone)
    user["balance"] += body.amount
    return {"phone": body.phone, "recharged": body.amount, "new_balance": user["balance"], "status": "success"}

# ──────────────────────────────────────────────
# ── SIM Card ──
# ──────────────────────────────────────────────

@app.get("/sim/{phone}", summary="Get SIM info")
def get_sim_info(phone: str):
    """اطلاعات سیم‌کارت"""
    if phone not in SIMS_DB:
        raise HTTPException(404, "SIM not found")
    sim = SIMS_DB[phone].copy()
    sim.pop("puk")  # never expose PUK in normal query
    return sim

@app.post("/sim/puk", summary="Retrieve PUK code after identity verification")
def get_puk(body: SimPukRequest):
    """دریافت کد PUK پس از تأیید هویت"""
    user = require_user(body.phone)
    if user["national_id"] != body.national_id:
        raise HTTPException(403, "Identity verification failed — national ID mismatch")
    sim = SIMS_DB.get(body.phone)
    if not sim:
        raise HTTPException(404, "SIM not found")
    sim["pin_blocked"] = False
    sim["status"] = "active"
    return {"phone": body.phone, "puk_code": sim["puk"], "message": "SIM unblocked. Use PUK to reset PIN."}

@app.post("/sim/{phone}/block", summary="Block SIM card")
def block_sim(phone: str):
    if phone not in SIMS_DB:
        raise HTTPException(404, "SIM not found")
    SIMS_DB[phone]["status"] = "blocked"
    return {"phone": phone, "status": "blocked", "message": "SIM card blocked successfully"}

@app.post("/sim/{phone}/unblock", summary="Unblock SIM card")
def unblock_sim(phone: str):
    if phone not in SIMS_DB:
        raise HTTPException(404, "SIM not found")
    SIMS_DB[phone]["status"] = "active"
    SIMS_DB[phone]["pin_blocked"] = False
    return {"phone": phone, "status": "active", "message": "SIM card unblocked successfully"}

# ──────────────────────────────────────────────
# ── Data Usage ──
# ──────────────────────────────────────────────

@app.get("/data/{phone}/usage", summary="Check internet data usage")
def check_data_usage(phone: str):
    """بررسی مصرف اینترنت"""
    require_user(phone)
    if phone not in DATA_USAGE_DB:
        raise HTTPException(404, "Data record not found")
    d = DATA_USAGE_DB[phone]
    remaining = round(d["total_gb"] - d["used_gb"], 2)
    pct = round((d["used_gb"] / d["total_gb"]) * 100, 1)
    return {
        "phone": phone,
        "total_gb": d["total_gb"],
        "used_gb": round(d["used_gb"], 2),
        "remaining_gb": remaining,
        "usage_percent": pct,
        "reset_date": d["reset_date"],
    }

@app.post("/data/limit", summary="Set data usage limit")
def set_data_limit(body: DataLimitRequest):
    require_user(body.phone)
    if body.phone not in DATA_USAGE_DB:
        raise HTTPException(404, "Data record not found")
    DATA_USAGE_DB[body.phone]["limit_gb"] = body.limit_gb
    return {"phone": body.phone, "limit_gb": body.limit_gb, "status": "limit set"}

# ──────────────────────────────────────────────
# ── Plans ──
# ──────────────────────────────────────────────

@app.get("/plans", summary="Get all available plans")
def get_plans():
    """لیست همه طرح‌های اشتراک"""
    return {"plans": list(PLANS_DB.values())}

@app.get("/plans/{plan_name}", summary="Get specific plan details")
def get_plan(plan_name: str):
    if plan_name not in PLANS_DB:
        raise HTTPException(404, f"Plan '{plan_name}' not found. Available: {list(PLANS_DB.keys())}")
    return PLANS_DB[plan_name]

@app.post("/plans/change", summary="Change subscription plan")
def change_plan(body: PlanChangeRequest):
    """تغییر طرح اشتراک"""
    user = require_user(body.phone)
    if body.new_plan not in PLANS_DB:
        raise HTTPException(400, f"Invalid plan. Choose from: {list(PLANS_DB.keys())}")
    old_plan = user["plan"]
    user["plan"] = body.new_plan
    new_data = PLANS_DB[body.new_plan]["data_gb"]
    DATA_USAGE_DB[body.phone]["total_gb"] = float(new_data)
    return {
        "phone": body.phone, "old_plan": old_plan,
        "new_plan": body.new_plan,
        "effective": "immediately",
        "new_monthly_price": PLANS_DB[body.new_plan]["price"],
    }

# ──────────────────────────────────────────────
# ── Call Services ──
# ──────────────────────────────────────────────

@app.post("/calls/block-number", summary="Block a phone number")
def block_number(body: BlockNumberRequest):
    """مسدود کردن یک شماره تلفن"""
    require_user(body.phone)
    if body.phone not in BLOCKLIST_DB:
        BLOCKLIST_DB[body.phone] = []
    if body.block_number in BLOCKLIST_DB[body.phone]:
        return {"message": f"{body.block_number} is already blocked", "blocklist": BLOCKLIST_DB[body.phone]}
    BLOCKLIST_DB[body.phone].append(body.block_number)
    return {"phone": body.phone, "blocked_number": body.block_number, "total_blocked": len(BLOCKLIST_DB[body.phone]), "status": "blocked"}

@app.get("/calls/blocklist/{phone}", summary="Get blocked numbers list")
def get_blocklist(phone: str):
    require_user(phone)
    return {"phone": phone, "blocked_numbers": BLOCKLIST_DB.get(phone, [])}

# ──────────────────────────────────────────────
# ── Complaints & Tickets ──
# ──────────────────────────────────────────────

@app.post("/complaints", status_code=201, summary="Submit a complaint")
def submit_complaint(body: ComplaintCreate):
    """ثبت شکایت"""
    require_user(body.phone)
    ticket_id = f"TKT-{str(uuid.uuid4())[:8].upper()}"
    ticket = {
        "id": ticket_id, "phone": body.phone,
        "subject": body.subject, "description": body.description,
        "status": "open", "priority": "normal",
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "estimated_resolution": (datetime.now() + timedelta(days=3)).strftime("%Y-%m-%d"),
    }
    TICKETS_DB[ticket_id] = ticket
    return ticket

@app.get("/complaints/{ticket_id}", summary="Track complaint status")
def track_complaint(ticket_id: str):
    """پیگیری وضعیت شکایت"""
    if ticket_id not in TICKETS_DB:
        raise HTTPException(404, "Ticket not found")
    return TICKETS_DB[ticket_id]

# ──────────────────────────────────────────────
# ── Account Management ──
# ──────────────────────────────────────────────

@app.post("/account/{phone}/suspend", summary="Suspend account")
def suspend_account(phone: str):
    user = require_user(phone)
    user["status"] = "suspended"
    return {"phone": phone, "status": "suspended", "message": "Account suspended successfully"}

@app.post("/account/{phone}/reactivate", summary="Reactivate account")
def reactivate_account(phone: str):
    user = require_user(phone)
    user["status"] = "active"
    return {"phone": phone, "status": "active", "message": "Account reactivated successfully"}

@app.get("/account/{phone}/info", summary="Get full account info")
def get_account_info(phone: str):
    """اطلاعات کامل حساب"""
    user = require_user(phone)
    sim  = SIMS_DB.get(phone, {})
    data = DATA_USAGE_DB.get(phone, {})
    plan = PLANS_DB.get(user["plan"], {})
    return {
        "user": user,
        "sim": {k: v for k, v in sim.items() if k != "puk"},
        "data_usage": data,
        "plan_details": plan,
    }

# ──────────────────────────────────────────────
# Health Check
# ──────────────────────────────────────────────

@app.get("/health")
def health():
    return {"status": "ok", "users": len(USERS_DB), "sims": len(SIMS_DB)}
