# ============================================================
# 🔐 UPSTOX AUTO TOKEN ENGINE – STABLE VERSION
# Handles access token refresh automatically
# ============================================================

import os
import time
import requests
from dotenv import load_dotenv

load_dotenv(override=True)


class UpstoxAuthEngine:

    BASE_URL = "https://api.upstox.com/v2"

    def __init__(self):
        self.env_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            ".env"
        )
        self.api_key = os.getenv("UPSTOX_API_KEY")
        self.api_secret = os.getenv("UPSTOX_API_SECRET")
        self.redirect_uri = os.getenv("UPSTOX_REDIRECT_URI")
        self.refresh_token = os.getenv("UPSTOX_REFRESH_TOKEN")
        self.manual_login_url = f"https://api.upstox.com/v2/login/authorization/dialog?response_type=code&client_id={self.api_key}&redirect_uri={self.redirect_uri}"

    # ============================================================
    # REFRESH ACCESS TOKEN
    # ============================================================

    def refresh_access_token(self):

        print("🔄 Refreshing Upstox Access Token...")

        url = f"{self.BASE_URL}/login/authorization/token"

        payload = {
            "grant_type": "refresh_token",
            "refresh_token": self.refresh_token,
            "client_id": self.api_key,
            "client_secret": self.api_secret,
            "redirect_uri": self.redirect_uri
        }

        try:
            response = requests.post(url, data=payload, timeout=15)
        except Exception as e:
            print(f"Token refresh request failed: {e}")
            return None

        if response.status_code == 200:
            data = response.json()

            new_access_token = data.get("access_token")
            new_refresh_token = data.get("refresh_token")

            if new_access_token:
                self.update_env(new_access_token, new_refresh_token)
                print("✅ Access Token Refreshed Successfully")
                return new_access_token
            else:
                print("❌ Access Token missing in response")
                return None

        else:
            print("❌ Token Refresh Failed:", response.text)
            return None

    # ============================================================
    # UPDATE .ENV FILE
    # ============================================================

    def update_env(self, access_token, refresh_token=None):
        env_path = self.env_path

        if not os.path.exists(env_path):
            print("❌ .env file not found")
            return

        with open(env_path, "r") as file:
            lines = file.readlines()

        with open(env_path, "w") as file:
            for line in lines:
                if line.startswith("UPSTOX_ACCESS_TOKEN="):
                    file.write(f"UPSTOX_ACCESS_TOKEN={access_token}\n")
                elif refresh_token and line.startswith("UPSTOX_REFRESH_TOKEN="):
                    file.write(f"UPSTOX_REFRESH_TOKEN={refresh_token}\n")
                else:
                    file.write(line)

        print(".env file updated with new tokens")

    def get_token_from_code(self, code):
        """Exchange auth code for access_token and refresh_token."""
        url = f"{self.BASE_URL}/login/authorization/token"
        payload = {
            "code": code,
            "client_id": self.api_key,
            "client_secret": self.api_secret,
            "redirect_uri": self.redirect_uri,
            "grant_type": "authorization_code"
        }
        
        try:
            response = requests.post(url, data=payload, timeout=15)
            if response.status_code == 200:
                data = response.json()
                access_token = data.get("access_token")
                refresh_token = data.get("refresh_token")
                if access_token:
                    self.update_env(access_token, refresh_token)
                    return access_token
            else:
                print(f"❌ Token Exchange Failed: {response.text}")
        except Exception as e:
            print(f"❌ Error during token exchange: {e}")
        return None

    def wait_for_manual_access_token(self, previous_token=None, poll_seconds=5, max_wait_seconds=900):
        # 🔥 Audit Item #4: Remove manual token dependency
        from core.unattended_auth_engine import UnattendedAuthEngine
        
        print("🤖 Attempting Zero-Touch Auto-Login...")
        auto_auth = UnattendedAuthEngine()
        success, msg = auto_auth.login()
        
        if success:
            print(f"✅ {msg}")
            # Re-load token from env
            load_dotenv(override=True)
            return os.getenv("UPSTOX_ACCESS_TOKEN")
        else:
            print(f"⚠️ Auto-Login Failed: {msg}")
            print("Manual token update required. Please generate a new access token and update .env")
            return None
