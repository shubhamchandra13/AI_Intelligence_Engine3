# ============================================================
# 📡 CENTRAL DATA FETCHER – SECURE VERSION
# Data Layer Abstraction
# ============================================================

import os
import requests
import pandas as pd
from datetime import datetime, timedelta
from dotenv import load_dotenv
from urllib.parse import quote
from core.upstox_client import UpstoxClient

load_dotenv()

BASE_URL = "https://api.upstox.com/v2"
ACCESS_TOKEN = os.getenv("UPSTOX_ACCESS_TOKEN")

HEADERS = {
    "Authorization": f"Bearer {ACCESS_TOKEN}",
    "Accept": "application/json"
}


INSTRUMENT_MAP = {
    "BANKNIFTY": "NSE_INDEX|Nifty Bank",
    "NIFTY": "NSE_INDEX|Nifty 50",
    "FINNIFTY": "NSE_INDEX|Nifty Fin Service",
    "MIDCAPNIFTY": "NSE_INDEX|NIFTY MIDCAP 100"
}


class DataFetcher:

    def __init__(self):
        # Reuse the auth-refreshing client for critical market-data fallbacks.
        self.upstox_client = None

    def _get_upstox_client(self):
        if self.upstox_client is None:
            try:
                self.upstox_client = UpstoxClient()
            except Exception:
                self.upstox_client = None
        return self.upstox_client

    def _get_headers(self):
        # Delegate to the robust client for the latest token
        client = self._get_upstox_client()
        if client and client.access_token:
            return {
                "Authorization": f"Bearer {client.access_token}",
                "Accept": "application/json"
            }
        
        # Fallback (only if client init failed)
        load_dotenv(override=True)
        token = os.getenv("UPSTOX_ACCESS_TOKEN")
        return {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json"
        }

    # ================================
    # SPOT PRICE
    # ================================
    def get_spot(self, symbol):

        instrument_key = INSTRUMENT_MAP.get(symbol)
        if not instrument_key:
            print(f"Invalid symbol: {symbol}")
            return None

        spot = self.get_option_ltp(instrument_key)
        if spot and spot > 0:
            return spot

        client = self._get_upstox_client()
        if client:
            spot = client.fetch_spot(instrument_key)
            if spot and spot > 0:
                return spot

        # Final fallback: use the latest intraday candle close so the UI and
        # analysis do not stay stuck at zero when LTP endpoint is flaky.
        candles = self.get_candles(symbol, interval="1minute", limit=2)
        if candles is not None and not candles.empty and "close" in candles.columns:
            try:
                close_price = float(candles["close"].iloc[-1])
                if close_price > 0:
                    return close_price
            except Exception:
                return None

        return None

    # ================================
    # OPTION INSTRUMENT KEY
    # ================================
    def get_option_instrument_key(self, symbol, strike, option_type, expiry):
        """
        Finds the instrument key for a specific option contract.
        """
        index_key = INSTRUMENT_MAP.get(symbol)
        if not index_key:
            return None

        url = f"{BASE_URL}/option/chain"

        try:
            response = requests.get(
                url,
                headers=self._get_headers(),
                params={"instrument_key": index_key, "expiry_date": expiry},
                timeout=15,
            )
            data = response.json()
        except Exception as e:
            print("Option Chain API Error:", e)
            return None

        if data.get("status") != "success":
            return None

        chain = data.get("data", [])
        for item in chain:
            if float(item.get("strike_price")) == float(strike):
                opt_data = item.get("call_options" if option_type.upper() == "CE" else "put_options")
                if opt_data:
                    return opt_data.get("instrument_key")
        
        return None

    # ================================
    # OPTION LTP
    # ================================
    def get_option_ltp(self, instrument_key):
        """
        Fetches the Last Traded Price for any instrument key.
        """
        if not instrument_key:
            return None

        url = f"{BASE_URL}/market-quote/ltp"

        try:
            response = requests.get(
                url,
                headers=self._get_headers(),
                params={"instrument_key": instrument_key},
                timeout=15,
            )
            data = response.json()
        except Exception as e:
            print("LTP API Error:", e)
            return None

        if data.get("status") != "success":
            return None

        data_block = data.get("data", {})
        if not data_block:
            return None

        first_key = list(data_block.keys())[0]
        return data_block[first_key]["last_price"]

    # ================================
    # BATCH LTP
    # ================================
    def get_ltps(self, instrument_keys):
        """
        Fetches LTP for multiple instrument keys at once.
        Ensures returned keys match input keys exactly.
        """
        if not instrument_keys:
            return {}

        # Remove duplicates and empty keys
        unique_keys = list(set([k for k in instrument_keys if k]))
        keys_str = ",".join(unique_keys)
        url = f"{BASE_URL}/market-quote/ltp"

        results = {}
        headers = self._get_headers()
        try:
            response = requests.get(
                url,
                headers=headers,
                params={"instrument_key": keys_str},
                timeout=15,
            )
            data = response.json()
            
            if data.get("status") == "success":
                data_block = data.get("data", {})
                for k in unique_keys:
                    val = data_block.get(k)
                    if val:
                        results[k] = val.get("last_price")
                    else:
                        results[k] = self.get_option_ltp(k)
            else:
                for k in unique_keys:
                    results[k] = self.get_option_ltp(k)
                    
        except Exception as e:
            print("Batch LTP API Error:", e)
            for k in unique_keys:
                results[k] = self.get_option_ltp(k)
        
        return results

    # ================================
    # ROBUST CANDLE FETCH (Level 8)
    # ================================
    def get_candles(self, symbol, interval="1minute", limit=500):
        instrument_key = INSTRUMENT_MAP.get(symbol)
        if not instrument_key: return None

        all_candles = []
        
        # 1. Pull Latest Intraday
        url_intra = f"{BASE_URL}/historical-candle/intraday/{instrument_key}/{interval}"
        try:
            resp = requests.get(url_intra, headers=self._get_headers())
            data = resp.json()
            if data.get("status") == "success":
                all_candles = data.get("data", {}).get("candles", [])
        except: pass

        # 2. Pull Historical if needed to fill limit
        if len(all_candles) < limit:
            to_date = datetime.now().strftime("%Y-%m-%d")
            from_date = (datetime.now() - timedelta(days=5)).strftime("%Y-%m-%d")
            url_hist = f"{BASE_URL}/historical-candle/{instrument_key}/{interval}/{to_date}/{from_date}"
            try:
                resp = requests.get(url_hist, headers=self._get_headers())
                data = resp.json()
                if data.get("status") == "success":
                    hist_candles = data.get("data", {}).get("candles", [])
                    all_candles.extend(hist_candles)
            except: pass

        if not all_candles: return None

        # Convert to DF and drop duplicates (sort by timestamp)
        df = pd.DataFrame(all_candles)
        # Unique by timestamp (column 0)
        df = df.drop_duplicates(subset=0).sort_values(0)
        
        if len(df.columns) >= 6:
            df = df.iloc[:, :6]
            df.columns = ["timestamp", "open", "high", "low", "close", "volume"]
        else:
            return None

        df["timestamp"] = pd.to_datetime(df["timestamp"])
        df = df.sort_values("timestamp").reset_index(drop=True)

        if len(df) > limit:
            df = df.tail(limit)

        return df
