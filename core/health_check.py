# ============================================================
# 🏥 SYSTEM HEALTH CHECK MODULE
# Audit Item #6: Startup diagnostics for production readiness
# ============================================================

import os
import sqlite3
import requests
import json
from core.upstox_client import UpstoxClient

class HealthCheck:
    def __init__(self, settings):
        self.settings = settings
        self.report = []
        self.critical_failure = False

    def check_internet(self):
        try:
            requests.get("https://api.upstox.com/v2/login", timeout=5)
            self.report.append("✅ Internet: Connected to Upstox API")
            return True
        except:
            self.report.append("❌ Internet: Connection Failed")
            self.critical_failure = True
            return False

    def check_db(self):
        db_path = "database/trades.db"
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            self.report.append(f"✅ Database: {db_path} is healthy")
            conn.close()
            return True
        except Exception as e:
            self.report.append(f"❌ Database: Integrity Error - {e}")
            self.critical_failure = True
            return False

    def check_broker_auth(self):
        try:
            client = UpstoxClient()
            profile = client.get_profile()
            if profile and profile.get("status") == "success":
                user_name = profile.get("data", {}).get("user_name", "Unknown")
                self.report.append(f"✅ Broker: Auth Valid (User: {user_name})")
                return True
            else:
                self.report.append("❌ Broker: Invalid Session / Token Expired")
                self.critical_failure = True
                return False
        except Exception as e:
            self.report.append(f"❌ Broker: Client Error - {e}")
            self.critical_failure = True
            return False

    def check_models(self):
        registry_path = "database/ml_model_registry.json"
        if os.path.exists(registry_path):
            try:
                with open(registry_path, "r") as f:
                    data = json.load(f)
                self.report.append("✅ AI Brain: Model Registry found")
                return True
            except:
                self.report.append("⚠️ AI Brain: Registry Corrupt (Will Auto-Fix)")
                return True
        else:
            self.report.append("⚠️ AI Brain: No Model Registry (First Run Mode)")
            return True

    def run_all(self):
        print("\n" + "═"*50)
        print("🏥 STARTUP DIAGNOSTICS (Level 7 Readiness)")
        print("═"*50)
        
        self.check_internet()
        self.check_db()
        self.check_broker_auth()
        self.check_models()

        for line in self.report:
            print(line)
        
        print("═"*50)
        
        if self.critical_failure:
            print("🛑 CRITICAL FAILURE: System cannot start safely.")
            return False
        
        print("🚀 ALL SYSTEMS NOMINAL. Booting Engine...\n")
        return True
