import asyncio
import os
import json
from datetime import datetime, timedelta
from dotenv import load_dotenv
from sqlmodel import SQLModel, create_engine, Session, select, func, or_
import google.generativeai as genai

# Setup Local Testing DB with all models
from models import Transaction, User, AuditLog, Milestone, VendorBill, Client, Employee, RecurringExpense, Budget

engine = create_engine("sqlite:///:memory:")
SQLModel.metadata.create_all(engine)

load_dotenv()
GEMINI_KEY = os.getenv("GEMINI_KEY")
genai.configure(api_key=GEMINI_KEY)

def seed_data():
    with Session(engine) as session:
        # Create User
        user = User(id=1, email="ceo@zetafin.app", password_hash="...", business_name="ZetaFin", industry="Fintech", bank_balance=5000000.0)
        session.add(user)
        
        # Add 100 random transactions
        for i in range(100):
            tx = Transaction(
                user_id=1,
                date=datetime.utcnow() - timedelta(days=i),
                description=f"Transaction {i} - General Expense",
                amount=-1000.0,
                type="expense",
                category="General"
            )
            session.add(tx)
        
        # Add the "Needle in the Haystack"
        needle = Transaction(
            user_id=1,
            date=datetime.utcnow() - timedelta(days=10),
            description="Special Payment from Ali Merchants for Alpha Project",
            amount=750000.0,
            type="income",
            category="Project Income"
        )
        session.add(needle)
        
        # Add a specific Audit Log
        audit = AuditLog(
            user_id=1,
            action="DELETE",
            table_name="Vendor Bill",
            record_id=999,
            timestamp=datetime.utcnow() - timedelta(days=2)
        )
        session.add(audit)
        
        session.commit()

async def query_local_bot(query: str):
    print(f"\n[USER]: {query}")
    from ai_consultant import get_ceo_summary, query_ai_insights
    with Session(engine) as session:
        # Show the "Deep Context" (Search Results) independently of Gemini
        summary = get_ceo_summary(session, 1)
        q = query.lower()
        stop_words = {"how", "much", "tell", "from", "with", "this", "that", "show", "what", "where", "when", "paisa", "kitna", "aya", "tha", "diya"}
        keywords = [w.strip("?,.!") for w in q.split() if len(w) > 2 and w not in stop_words]
        
        print(f"SEARCH KEYWORDS: {keywords}")
        
        # Now call the actual logic
        answer = await query_ai_insights(query, session, 1)
        print(f"[ZETAFIN AI]: {answer}")

async def run_volume_test():
    print("--- STARTING INFINITE-SCALE VOLUME TEST ---")
    seed_data()
    
    # Just one query to avoid 429 and prove the logic
    await query_local_bot("Ali merchants se kitna paisa aya?")

if __name__ == "__main__":
    asyncio.run(run_volume_test())
