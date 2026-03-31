from sqlmodel import Session, select, func
from models import Transaction, Milestone, VendorBill, RecurringExpense, User, AuditLog, Budget
from datetime import datetime, timedelta
import json
import httpx

# Shared keys from main.py
import os
from dotenv import load_dotenv

load_dotenv()

XAI_KEY = os.getenv("XAI_KEY", "")
OPENROUTER_KEY = os.getenv("OPENROUTER_KEY", "")

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

async def query_ai_insights(query: str, db: Session, user_id: int):
    summary = get_ceo_summary(db, user_id)
    
    prompt = f"""
    You are the ZetaFin AI Financial Consultant. Answer the CEO's question based on their real financial data.
    Be concise, professional, and strategic.
    
    Current Financial Summary:
    - Bank Balance: {summary['balance']} {summary['currency']}
    - Total Receivables (Clients): {summary['receivables']} {summary['currency']}
    - Total Payables (Vendors): {summary['payables']} {summary['currency']}
    - 30-Day Burn Rate: {summary['monthly_burn']} {summary['currency']}
    - Category Budgets: {json.dumps(summary['budgets'])}
    - Actual Spend per Category: {json.dumps(summary['actual_spending'])}
    
    CEO Question: {query}
    
    Strategic Insight:
    """
    
    # Reuse Grok-beta (Primary) or Mini (Fallback) logic
    async with httpx.AsyncClient() as client:
        try:
            # Try xAI
            resp = await client.post(
                "https://api.x.ai/v1/chat/completions",
                json={"model": "grok-beta", "messages": [{"role": "user", "content": prompt}]},
                headers={"Authorization": f"Bearer {XAI_KEY}", "Content-Type": "application/json"},
                timeout=20.0
            )
            if resp.status_code == 200:
                return resp.json()["choices"][0]["message"]["content"]
        except:
            pass
            
        try:
            # Try OpenRouter
            resp = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                json={"model": "openai/gpt-4o-mini", "messages": [{"role": "user", "content": prompt}]},
                headers={"Authorization": f"Bearer {OPENROUTER_KEY}", "Content-Type": "application/json"},
                timeout=20.0
            )
            if resp.status_code == 200:
                return resp.json()["choices"][0]["message"]["content"]
        except:
            return "ZetaFin AI is currently resting. Please try again in 1 minute."

    return "ZetaFin AI is taking a coffee break. Please try again later."

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
