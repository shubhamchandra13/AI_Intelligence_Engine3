import os
import json
import sqlite3
import requests
from datetime import datetime
from dotenv import load_dotenv
from core.runtime_control import read_runtime_state, read_control_state

# Path to .env file relative to this script
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
env_path = os.path.join(BASE_DIR, '.env')
load_dotenv(dotenv_path=env_path)

class GeminiAIAgent:
    """
    AI Agent powered by Google Gemini (Latest Stable)
    """
    def __init__(self, model="gemini-2.0-flash"):
        # Strip to remove any accidental spaces or newlines
        self.api_key = (os.getenv("GEMINI_API_KEY") or "").strip()
        self.model = model
        # Using v1beta which is the most reliable for current Gemini models
        self.base_url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={self.api_key}"
        self.db_path = os.path.join(BASE_DIR, "database", "trades.db")
        self.logs_path = os.path.join(BASE_DIR, "watchdog_log.txt")

    def _get_system_context(self):
        runtime = read_runtime_state() or {}
        control = read_control_state() or {}
        
        trades = []
        try:
            conn = sqlite3.connect(self.db_path)
            cur = conn.cursor()
            cur.execute("SELECT index_name, direction, entry_price, pnl, timestamp FROM trades ORDER BY id DESC LIMIT 5")
            trades = cur.fetchall()
            conn.close()
        except Exception:
            trades = []

        logs = ""
        try:
            if os.path.exists(self.logs_path):
                with open(self.logs_path, "r") as f:
                    logs = "".join(f.readlines()[-15:])
        except Exception:
            logs = ""

        return {
            "current_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "system_status": runtime.get("system_status", "UNKNOWN"),
            "best_index": runtime.get("best_index", "N/A"),
            "open_position": bool(runtime.get("position")),
            "recent_trades": trades,
            "recent_logs": logs,
            "overrides": control.get("overrides", {})
        }

    def chat(self, user_query):
        if not self.api_key:
            return "Error: GEMINI_API_KEY is missing in .env file."

        print(f"DEBUG: Calling Gemini API with model: {self.model}")
        context = self._get_system_context()
        
        system_prompt = f"""
        You are 'AI Intelligence Assistant', the brain of an Institutional Trading System.
        Current System State: {json.dumps(context)}
        Communicating in Hinglish (Hindi + English).
        
        Capabilities: Analyze market, explain trades, suggest bug fixes from logs.
        """

        payload = {
            "contents": [{
                "parts": [{"text": f"{system_prompt}\n\nUser: {user_query}"}]
            }]
        }

        try:
            response = requests.post(self.base_url, json=payload, timeout=30)
            
            if response.status_code == 200:
                res_json = response.json()
                return res_json['candidates'][0]['content']['parts'][0]['text']
            else:
                # Log the actual error for debugging
                err_data = {}
                try:
                    err_data = response.json()
                except Exception:
                    err_data = {}
                
                err_msg = err_data.get("error", {}).get("message", "Unknown Error")
                err_status = err_data.get("error", {}).get("status", f"Status {response.status_code}")
                
                print(f"DEBUG: Gemini Error ({err_status}): {err_msg}")
                return f"Gemini API {err_status}. {err_msg[:50]}..."
                
        except Exception as e:
            return f"Connection Error: {str(e)}"

if __name__ == "__main__":
    agent = GeminiAIAgent()
    print(agent.chat("Hi"))
