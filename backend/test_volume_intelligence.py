import asyncio
import os
import json
from datetime import datetime, timedelta
from dotenv import load_dotenv
from sqlmodel import SQLModel, create_engine, Session, select, func, or_
import google.generativeai as genai

# Import models from our existing project
from models import Transaction, User, AuditLog, Milestone, VendorBill

# Setup Local Testing DB
engine = create_engine("sqlite:///:memory:")
SQLModel.metadata.create_all(engine)

load_dotenv()
GEMINI_KEY = os.getenv("GEMINI_KEY")
genai.configure(api_key=GEMINI_KEY)

def seed_data():
    with Session(engine) as session:
        # Create User
        user = User(id=1, email="ceo@zetafin.app", hashed_password="...", bank_balance=5000000.0)
        session.merge(user)
        
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
            description="Special Payment to Ali Merchants for Alpha Project",
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
    from ai_consultant import query_ai_insights
    with Session(engine) as session:
        answer = await query_ai_insights(query, session, 1)
        print(f"[ZETAFIN AI]: {answer}")

async def run_volume_test():
    print("--- STARTING INFINITE-SCALE VOLUME TEST ---")
    seed_data()
    
    # 1. Test Roman Urdu search for the "Needle"
    await query_local_bot("Ali merchants se kitna paisa aya tha?")
    
    # 2. Test Audit Log awareness
    await query_local_bot("Who deleted the vendor bill recently?")
    
    # 3. Test general awareness in English
    await query_local_bot("What is my current total bank balance?")

if __name__ == "__main__":
    asyncio.run(run_volume_test())
