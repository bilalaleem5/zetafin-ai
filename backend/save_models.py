import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_KEY"))

with open("available_models.txt", "w") as f:
    for m in genai.list_models():
        f.write(f"{m.name}\n")
