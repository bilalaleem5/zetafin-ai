import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv("backend/.env")
GEMINI_KEY = os.getenv("GEMINI_KEY", "")

if GEMINI_KEY:
    genai.configure(api_key=GEMINI_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')
    try:
        response = model.generate_content("Hello! Are you working?")
        print(f"Success: {response.text}")
    except Exception as e:
        print(f"Error: {e}")
else:
    print("No GEMINI_KEY found in .env")
