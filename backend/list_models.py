import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
GEMINI_KEY = os.getenv("GEMINI_KEY")
genai.configure(api_key=GEMINI_KEY)

try:
    for m in genai.list_models():
        print(m.name)
except Exception as e:
    print(f"Error: {e}")
