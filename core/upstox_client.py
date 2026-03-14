# ============================================================
# 🚀 UPSTOX CLIENT – STABLE VERSION (AUTO EXPIRY STORED)
# ============================================================

import os
import requests
from dotenv import load_dotenv
from core.upstox_auth_engine import UpstoxAuthEngine

load_dotenv(override=True)


class UpstoxClient:

    BASE_URL = "https://api.upstox.com/v2"

    def __init__(self):
        self.access_token = os.getenv("UPSTOX_ACCESS_TOKEN")

        if not self.access_token:
            raise Exception("❌ UPSTOX_ACCESS_TOKEN missing in .env")

        self.auth_engine = UpstoxAuthEngine()

        # ✅ Store selected expiry here (UI stable)
        self.last_selected_expiry = None
        self.last_status = "INITIALIZING"

    @property
    def status(self):
        return self.last_status

    @property
    def expiry(self):
        return self.last_selected_expiry

    # ============================================================
    # INTERNAL REQUEST HANDLER
    # ============================================================

    def _make_request(self, endpoint, method="GET", payload=None, retry_count=0):
        # Optimization: Only reload token if we suspect it changed externally or on first load,
        # but for high-freq trading, we rely on memory state + 401 handling.
        
        url = f"{self.BASE_URL}{endpoint}"

        headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }

        def send_request():
            if method == "GET":
                return requests.get(url, headers=headers, timeout=15)
            return requests.post(url, json=payload, headers=headers, timeout=15)

        try:
            response = send_request()
            if response.status_code == 200:
                self.last_status = "CONNECTED"
        except Exception as e:
            self.last_status = f"API ERROR: {e}"
            return None

        # HANDLE TOKEN EXPIRY (401)
        if response.status_code == 401:
            if retry_count >= 1:
                self.last_status = "TOKEN REFRESH FAILED (Recursion Limit)"
                return None
                
            self.last_status = "TOKEN EXPIRED"
            print("⚠️ Upstox Token Expired. Refreshing...")
            
            new_token = self.auth_engine.refresh_access_token()
            if not new_token:
                # Fallback: Wait for manual
                new_token = self.auth_engine.wait_for_manual_access_token(
                    previous_token=self.access_token
                )
            
            if new_token:
                self.access_token = new_token
                self.last_status = "TOKEN REFRESHED"
                # Retry request ONCE with new token
                return self._make_request(endpoint, method, payload, retry_count=retry_count + 1)
            else:
                self.last_status = "MANUAL LOGIN REQUIRED"
                return None

        if response.status_code != 200:
            self.last_status = f"HTTP {response.status_code}"
            # Optional: Log body for debugging
            # print(f"API Error Body: {response.text}")
            return None

        try:
            return response.json()
        except:
            return None

    def exchange_code_for_token(self, code):
        """Proxy to auth_engine to update tokens."""
        token = self.auth_engine.get_token_from_code(code)
        if token:
            self.access_token = token
            self.last_status = "TOKEN UPDATED"
            return True
        return False

    # ============================================================
    # FETCH USER PROFILE (Audit Item #6)
    # ============================================================

    def get_profile(self):
        """
        Fetches user profile to verify authentication status.
        """
        endpoint = "/user/profile"
        return self._make_request(endpoint)

    # ============================================================
    # FETCH SPOT PRICE
    # ============================================================

    def fetch_spot(self, instrument_key):

        endpoint = f"/market-quote/ltp?instrument_key={instrument_key}"
        data = self._make_request(endpoint)

        if data and "data" in data and data["data"]:
            try:
                first_key = list(data["data"].keys())[0]
                quote = data["data"][first_key]
                return quote.get("last_price") or quote.get("ltp")
            except:
                return None

        return None

    # ============================================================
    # FETCH MARKET DEPTH (L2 DATA)
    # ============================================================

    def fetch_market_depth(self, instrument_key):
        """
        Fetches full market quote including top 5 bids and asks.
        """
        endpoint = f"/market-quote/quotes?instrument_key={instrument_key}"
        data = self._make_request(endpoint)

        if data and "data" in data and data["data"]:
            try:
                first_key = list(data["data"].keys())[0]
                return data["data"][first_key].get("depth")
            except:
                return None
        return None

    # ============================================================
    # FETCH OPTION CHAIN (AUTO EXPIRY SAFE)
    # ============================================================

    def fetch_option_chain(self, instrument_key, expiry_date=None):

        # 🔥 AUTO EXPIRY DETECTION
        if expiry_date is None:
            expiries = self.get_all_expiries(instrument_key)
            if not expiries:
                return None
            
            expiry_date = expiries[0]
            self.last_selected_expiry = expiry_date

        endpoint = f"/option/chain?instrument_key={instrument_key}&expiry_date={expiry_date}"
        data = self._make_request(endpoint)

        if not data or "data" not in data:
            return None

        return data["data"]

    def get_all_expiries(self, instrument_key):
        """
        Fetches all available expiry dates for an instrument.
        """
        expiry_endpoint = f"/option/contract?instrument_key={instrument_key}"
        expiry_data = self._make_request(expiry_endpoint)

        if not expiry_data or "data" not in expiry_data:
            return []

        try:
            contracts = expiry_data["data"]
            if not contracts:
                return []

            expiries = list(set(item["expiry"] for item in contracts if "expiry" in item))
            expiries.sort()
            return expiries
        except:
            return []
