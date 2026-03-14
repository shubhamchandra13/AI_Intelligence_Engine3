import os
import requests
from dotenv import load_dotenv

load_dotenv()

api_key = (os.getenv("GEMINI_API_KEY") or "").strip()
if not api_key:
    print("Error: GEMINI_API_KEY not found in .env")
    exit()

url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"

print(f"Fetching available models for key: {api_key[:10]}...")

try:
    response = requests.get(url)
    if response.status_code == 200:
        models = response.json().get('models', [])
        print("\nAvailable Models for your API Key:")
        print("-" * 50)
        for m in models:
            if "generateContent" in m.get("supportedGenerationMethods", []):
                print(f"Model: {m['name']}")
        print("-" * 50)
    else:
        print(f"Error {response.status_code}: {response.text}")
except Exception as e:
    print(f"Connection Error: {e}")
