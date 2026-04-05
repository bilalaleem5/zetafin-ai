import asyncio
import os
import json
from dotenv import load_dotenv
import google.generativeai as genai

# Load our new Gemini key
load_dotenv()
GEMINI_KEY = os.getenv("GEMINI_KEY", "")
genai.configure(api_key=GEMINI_KEY)

# Mock Summary Data (Sample of what the system would send)
MOCK_SUMMARY = {
    "balance": 1250000.0,
    "receivables": 450000.0,
    "payables": 120000.0,
    "monthly_burn": 85000.0,
    "currency": "PKR",
    "recent_transactions": [
        {"date": "2024-04-03", "desc": "Payment from Ali Merchants", "amt": 150000.0, "type": "income"},
        {"date": "2024-04-01", "desc": "Office Rent April", "amt": -45000.0, "type": "expense"},
        {"date": "2024-03-28", "desc": "Salary - Rehan Ahmed", "amt": -65000.0, "type": "expense"}
    ],
    "recent_audits": [
        {"time": "2024-04-04 11:20", "action": "EDIT", "item": "Transaction (ID: 45)"},
        {"time": "2024-04-02 09:15", "action": "DELETE", "item": "Vendor Bill (Saeed Co)"}
    ],
    "counts": {"clients": 12, "employees": 8}
}

async def test_query(query: str):
    print(f"\n[USER]: {query}")
    await asyncio.sleep(2)
    
    prompt = f"User asks: {query}. System Data: {json.dumps(MOCK_SUMMARY)}. Respond in same language."
    
    models = [m.name for m in genai.list_models() if "generateContent" in m.supported_generation_methods]
    for m_name in models:
        try:
            model = genai.GenerativeModel(m_name)
            response = model.generate_content(prompt)
            print(f"[DEBUG]: Worked with {m_name}")
            print(f"[ZETAFIN AI]: {response.text.strip()}")
            return # Success
        except Exception as e:
            continue
    print("[ERROR]: No working models found.")

async def run_tests():
    print("--- STARTING ROBUST INTELLIGENCE TEST ---")
    await test_query("Mera balance kitna hai?")
    await test_query("What was the last payment to Ali?")

if __name__ == "__main__":
    asyncio.run(run_tests())

async def run_tests():
    print("--- STARTING INTELLIGENCE TEST ---")
    
    # Test 1: Specific History in English
    await test_query("How much did we pay for rent lately?")
    
    # Test 2: Roman Urdu and Specific Entity
    await test_query("Ali merchants se kitna paisa aya tha aur kab?")
    
    # Test 3: Language Switching
    await test_query("Mera total bank balance kya hai aur net position?")
    
    # Test 4: Detail Check
    await test_query("What was the last thing deleted from the system?")

if __name__ == "__main__":
    asyncio.run(run_tests())
