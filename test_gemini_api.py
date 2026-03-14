import os
import requests
from dotenv import load_dotenv

# Path to .env file relative to this script
env_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(dotenv_path=env_path)

api_key = (os.getenv("GEMINI_API_KEY") or "").strip()
model = "gemini-pro-latest"
base_url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"

payload = {
    "contents": [{
        "parts": [{"text": "Hello, are you there?"}]
    }]
}

print(f"Testing Gemini API with model: {model}")
print(f"URL: https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key=HIDDEN")

try:
    response = requests.post(base_url, json=payload, timeout=30)
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        print("Success!")
        print(response.json()['candidates'][0]['content']['parts'][0]['text'])
    else:
        print(f"Error: {response.text}")
except Exception as e:
    print(f"Exception: {e}")
