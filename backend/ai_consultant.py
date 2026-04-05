from sqlmodel import Session, select, func
from models import Transaction, Milestone, VendorBill, RecurringExpense, User, AuditLog, Budget
from datetime import datetime, timedelta
import json
import httpx
import google.generativeai as genai

# Shared keys from main.py
import os
from dotenv import load_dotenv

load_dotenv()

XAI_KEY = os.getenv("XAI_KEY", "")
OPENROUTER_KEY = os.getenv("OPENROUTER_KEY", "")
GEMINI_KEY = os.getenv("GEMINI_KEY", "")

if GEMINI_KEY:
    genai.configure(api_key=GEMINI_KEY)

def get_ceo_summary(db: Session, user_id: int):
    # 1. Financial totals
    user = db.get(User, user_id)
    balance = user.bank_balance if user else 0
    
    # Receivables (Pending Milestones)
    receivables = db.exec(select(func.sum(Milestone.amount)).where(Milestone.user_id == user_id, Milestone.status != "Paid")).one() or 0
    
    # Payables (Pending Vendor Bills)
    payables = db.exec(select(func.sum(VendorBill.amount)).where(VendorBill.user_id == user_id, VendorBill.status != "Paid")).one() or 0
    
    # 30-day Burn Rate (Manual Expenses + Paid Vendor Bills)
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    burn = db.exec(select(func.sum(Transaction.amount)).where(
        Transaction.user_id == user_id, 
        Transaction.type == "expense",
        Transaction.date >= thirty_days_ago
    )).one() or 0
    
    # Monthly Budget vs Actual
    current_month = datetime.utcnow().strftime("%Y-%m")
    budgets = db.exec(select(Budget).where(Budget.user_id == user_id, Budget.month == current_month)).all()
    budget_map = {b.category: b.amount for b in budgets}
    
    # Category spending for current month
    first_of_month = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    expenses = db.exec(select(Transaction.category, func.sum(Transaction.amount)).where(
        Transaction.user_id == user_id,
        Transaction.type == "expense",
        Transaction.date >= first_of_month
    ).group_by(Transaction.category)).all()
    
    actual_spending = {cat: amt for cat, amt in expenses}

    return {
        "balance": balance,
        "receivables": receivables,
        "payables": payables,
        "monthly_burn": burn,
        "budgets": budget_map,
        "actual_spending": actual_spending,
        "currency": user.currency if user else "PKR"
    }

import re

async def query_ai_insights(query: str, db: Session, user_id: int):
    # Fetch accurate real-time dashboard stats
    summary = get_ceo_summary(db, user_id)
    q = query.lower()
    
    currency = summary.get("currency", "PKR")
    
    # 1. Intent: Bank Balance
    if re.search(r'\b(balance|kitna paisa|bank|bachat|available|amount|cash)\b', q):
        return f"Aapka current bank balance {summary['balance']} {currency} hai."
        
    # 2. Intent: Receivables / Incomes Pending
    elif re.search(r'\b(receive|lena|lene|receivables|milna|milne|aana|aane)\b', q):
        return f"Aapne clients se total {summary['receivables']} {currency} lene hain (Pending Receivables)."
        
    # 3. Intent: Payables / Outstanding Bills
    elif re.search(r'\b(payable|dena|dene|vendors|bill|bills|udhar|qarza)\b', q):
        return f"Aapne vendors ko total {summary['payables']} {currency} dene hain (Pending Payables)."
        
    # 4. Intent: Expenses / Spends
    elif re.search(r'\b(expense|expenses|kharch|kharcha|burn|spend|kharach|lagaya|karch)\b', q):
        categories = summary.get('actual_spending', {})
        resp = f"Aapka pichle 30 din ka total kharcha {summary['monthly_burn']} {currency} aya hai.\n\n"
        if categories:
            resp += "Is maheenay ki category-wise details:\n"
            for cat, amt in categories.items():
                resp += f"- {cat}: {amt} {currency}\n"
        return resp.strip()
        
    # 5. Intent: Budgets
    elif re.search(r'\b(budget|limit|limits)\b', q):
        budgets = summary.get('budgets', {})
        if not budgets:
            return "Aapne is maheenay ka koi budget set nahi kiya hua."
        resp = "Aapke tay karda budgets ye hain:\n"
        for cat, amt in budgets.items():
            resp += f"- {cat}: {amt} {currency}\n"
        return resp.strip()
        
    # 6. Fallback: Full Dashboard Mini-Summary (Triggered on unrecognized queries like greetings)
    fallback_text = f"""
Main aapka local automated Financial Consultant hoon! Yeh aapke current dashboard key stats hain:

💰 **Bank Balance:** {summary['balance']} {currency}
📉 **Pichle 30 Din ka Kharcha:** {summary['monthly_burn']} {currency}
📥 **Milne Wali Raqam (Receivables):** {summary['receivables']} {currency}
📤 **Dene Wali Raqam (Payables):** {summary['payables']} {currency}

Aap specific report k liye pooch sakte hain (Misal ke tor par: "Mera expense kitna hai?" ya "Balance kya hai?").
"""
    return fallback_text.strip()

def log_audit(db: Session, user_id: int, action: str, table: str, record_id: int, old_val=None, new_val=None):
    log = AuditLog(
        user_id=user_id,
        action=action,
        table_name=table,
        record_id=record_id,
        old_values=json.dumps(old_val) if old_val else None,
        new_values=json.dumps(new_val) if new_val else None,
        timestamp=datetime.utcnow()
    )
    db.add(log)
    db.commit()
