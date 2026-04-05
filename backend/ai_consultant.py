from sqlmodel import Session, select, func
from models import Transaction, Milestone, VendorBill, RecurringExpense, User, AuditLog, Budget, Client, Employee
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
    print(f"DEBUG: GEMINI_KEY is loaded ({GEMINI_KEY[:10]}...)")
    genai.configure(api_key=GEMINI_KEY)
else:
    print("DEBUG: GEMINI_KEY is MISSING!")

def get_ceo_summary(db: Session, user_id: int):
    # 1. Financial totals
    user = db.get(User, user_id)
    balance = user.bank_balance if user else 0
    
    # Receivables (Pending Milestones)
    receivables = db.exec(select(func.sum(Milestone.amount)).where(Milestone.user_id == user_id, Milestone.status != "Paid")).one() or 0
    
    # Payables (Pending Vendor Bills)
    payables = db.exec(select(func.sum(VendorBill.amount)).where(VendorBill.user_id == user_id, VendorBill.status != "Paid")).one() or 0
    
    # 30-day Burn Rate
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    burn = db.exec(select(func.sum(Transaction.amount)).where(
        Transaction.user_id == user_id, 
        Transaction.type == "expense",
        Transaction.date >= thirty_days_ago
    )).one() or 0
    
    # Category spending for current month
    first_of_month = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    expenses = db.exec(select(Transaction.category, func.sum(Transaction.amount)).where(
        Transaction.user_id == user_id,
        Transaction.type == "expense",
        Transaction.date >= first_of_month
    ).group_by(Transaction.category)).all()
    actual_spending = {cat: amt for cat, amt in expenses}

    # NEW: Granular Context for AI "Intelligence"
    # Latest 15 transactions
    recent_txs = db.exec(select(Transaction).where(Transaction.user_id == user_id).order_by(Transaction.date.desc()).limit(15)).all()
    tx_list = [{"date": t.date.strftime('%Y-%m-%d'), "desc": t.description, "amt": t.amount, "type": t.type} for t in recent_txs]

    # Latest 10 Audit Logs (What happened?)
    recent_audits = db.exec(select(AuditLog).where(AuditLog.user_id == user_id).order_by(AuditLog.timestamp.desc()).limit(10)).all()
    audit_list = [{"time": a.timestamp.strftime('%Y-%m-%d %H:%M'), "action": a.action, "item": a.table_name} for a in recent_audits]

    # Entity Counts
    client_count = db.exec(select(func.count(Client.id)).where(Client.user_id == user_id)).one() or 0
    employee_count = db.exec(select(func.count(Employee.id)).where(Employee.user_id == user_id)).one() or 0

    return {
        "balance": balance,
        "receivables": receivables,
        "payables": payables,
        "monthly_burn": burn,
        "actual_spending": actual_spending,
        "currency": user.currency if user else "PKR",
        "recent_transactions": tx_list,
        "recent_audits": audit_list,
        "counts": {"clients": client_count, "employees": employee_count}
    }

async def query_ai_insights(query: str, db: Session, user_id: int):
    # 1. Basic Summary Context
    summary = get_ceo_summary(db, user_id)
    q = query.lower()
    
    # 2. DYNAMIC SEARCH LAYER (The "All-Knowing" part)
    # Extract keywords for deep DB search (exclude common filler words)
    stop_words = {"how", "much", "tell", "from", "with", "this", "that", "show", "what", "where", "when", "paisa", "kitna", "aya", "tha", "diya"}
    keywords = [w.strip("?,.!") for w in q.split() if len(w) > 2 and w not in stop_words]
    
    deep_context = []
    if keywords:
        from sqlmodel import or_
        # Search Transactions (Decription & Category)
        tx_filters = [Transaction.description.ilike(f"%{w}%") for w in keywords]
        tx_filters += [Transaction.category.ilike(f"%{w}%") for w in keywords]
        matching_txs = db.exec(select(Transaction).where(Transaction.user_id == user_id, or_(*tx_filters)).order_by(Transaction.date.desc()).limit(30)).all()
        for t in matching_txs:
            deep_context.append(f"Transaction: {t.date.strftime('%Y-%m-%d')} - {t.description} ({t.type}) - Amount: {t.amount}")

        # Search Audit Logs (Action & Item)
        audit_filters = [AuditLog.action.ilike(f"%{w}%") for w in keywords]
        audit_filters += [AuditLog.table_name.ilike(f"%{w}%") for w in keywords]
        matching_audits = db.exec(select(AuditLog).where(AuditLog.user_id == user_id, or_(*audit_filters)).order_by(AuditLog.timestamp.desc()).limit(15)).all()
        for a in matching_audits:
            deep_context.append(f"System Action: {a.timestamp.strftime('%Y-%m-%d %H:%M')} - {a.action} on {a.table_name} (ID: {a.record_id})")

        # Search Milestones/Bills for names
        bill_filters = [VendorBill.title.ilike(f"%{w}%") for w in keywords]
        matching_bills = db.exec(select(VendorBill).where(VendorBill.user_id == user_id, or_(*bill_filters)).limit(10)).all()
        for b in matching_bills:
            deep_context.append(f"Pending Bill: {b.title} - Amount: {b.amount} - Status: {b.status}")
        
    if deep_context:
        print(f"DEBUG: Found {len(deep_context)} relevant records for query.")
        for item in deep_context[:3]: print(f"  - {item}")

    # 3. Build Intelligent Prompt
    prompt = f"""
    You are the ZetaFin AI Financial Consultant. You have access to millions of records via a dynamic search engine.
    The CEO is asking a question. Use the provided GLOBAL TOTALS and matching DEEP CONTEXT to answer.
    
    RULES:
    1. MATCH LANGUAGE: Respond in the EXACT language/style of the user (Roman Urdu -> Roman Urdu, English -> English).
    2. DATA-DRIVEN: Use the 'Deep Context' below to find specific dates, names, or actions.
    3. NO HALLUCINATION: If the data isn't in 'Deep Context', say you couldn't find that specific record.
    
    GLOBAL TOTALS:
    - Balance: {summary['balance']} {summary['currency']}
    - Receivables: {summary['receivables']} {summary['currency']}
    - Payables: {summary['payables']} {summary['currency']}
    
    DEEP CONTEXT (Specific matches from DB):
    {chr(10).join(deep_context) if deep_context else "No specific matches found for keywords."}
    
    USER QUERY: {query}
    
    RESPONSE:
    """
    
    # 4. Call Gemini (Adaptive Intelligence)
    if GEMINI_KEY:
        try:
            model = genai.GenerativeModel('models/gemini-1.5-flash')
            response = model.generate_content(prompt)
            if response.text:
                return response.text.strip()
        except Exception as e:
            print(f"Gemini Intelligence Error (Flash): {e}")
            try:
                model = genai.GenerativeModel('models/gemini-pro')
                response = model.generate_content(prompt)
                return response.text.strip()
            except Exception as e2:
                print(f"Gemini Intelligence Error (Pro): {e2}")
                pass

    return "ZetaFin AI is temporarily resting. Please try again soon."

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
