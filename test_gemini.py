import asyncio
import os
import sys

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from backend.main import fetch_ai_parsing

async def test_parsing():
    print("Testing Gemini-powered CSV parsing...")
    sample_csv = "Date,Description,Amount\n2024-03-01,Test Income,500.0\n2024-03-02,Test Expense,-200.0"
    
    import time
    start = time.time()
    result = await fetch_ai_parsing(sample_csv)
    end = time.time()
    
    print(f"Time taken: {end - start:.2f} seconds")
    print(f"Result: {result}")

if __name__ == "__main__":
    asyncio.run(test_parsing())
