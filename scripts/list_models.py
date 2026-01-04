
import os
import google.generativeai as genai
from dotenv import load_dotenv
from pathlib import Path

load_dotenv(Path(__file__).parent.parent / ".env")
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))

print("Available models:")
for m in genai.list_models():
    if 'generateContent' in m.supported_generation_methods:
        print(m.name)








