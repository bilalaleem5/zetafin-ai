import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
GEMINI_KEY = os.getenv("GEMINI_KEY")
genai.configure(api_key=GEMINI_KEY)

print("Starting Exhaustive Model Test...")
for m in genai.list_models():
    if 'generateContent' in m.supported_generation_methods:
        print(f"Testing {m.name}...")
        try:
            model = genai.GenerativeModel(m.name)
            response = model.generate_content("Hi")
            print(f"SUCCESS: {m.name} works! Response: {response.text.strip()}")
        except Exception as e:
            print(f"FAILED: {m.name} - {e}")
