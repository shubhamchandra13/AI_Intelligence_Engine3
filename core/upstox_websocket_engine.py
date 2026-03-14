# ============================================================
# ⚡ UPSTOX WEBSOCKET ENGINE – REAL-TIME DATA STREAM
# High-Speed Data Layer for Institutional Execution
# ============================================================

import os
import json
import threading
import time
import websocket
import ssl
from dotenv import load_dotenv

load_dotenv(override=True)

class UpstoxWebsocketEngine:
    def __init__(self, instrument_keys):
        self.access_token = os.getenv("UPSTOX_ACCESS_TOKEN")
        self.instrument_keys = instrument_keys
        self.ws = None
        self.data_store = {key: {"ltp": 0.0, "v": 0} for key in instrument_keys}
        self.lock = threading.Lock()
        self.is_connected = False
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 10

    def _get_ws_url(self):
        # Upstox V2 Feed API URL
        return f"wss://api.upstox.com/v2/feed/market-data-feed"

    def on_message(self, ws, message):
        # Decode Binary Message (Upstox uses Protobuf-like binary or JSON depending on config)
        # For simplicity in this implementation, we assume JSON if possible or handle raw
        try:
            data = json.loads(message)
            if "data" in data:
                with self.lock:
                    for key, val in data["data"].items():
                        if key in self.data_store:
                            self.data_store[key]["ltp"] = val.get("ltp", self.data_store[key]["ltp"])
                            self.data_store[key]["v"] = val.get("v", self.data_store[key]["v"])
        except Exception as e:
            pass

    def on_error(self, ws, error):
        self.is_connected = False

    def on_close(self, ws, close_status_code, close_msg):
        self.is_connected = False

    def on_open(self, ws):
        self.is_connected = True
        self.reconnect_attempts = 0
        # Subscribe to instruments
        payload = {
            "guid": "guid",
            "method": "sub",
            "data": {
                "mode": "ltp", # 'full' for orderbook data
                "instrument_keys": self.instrument_keys
            }
        }
        ws.send(json.dumps(payload))

    def start(self):
        def run():
            while self.reconnect_attempts < self.max_reconnect_attempts:
                try:
                    self.ws = websocket.WebSocketApp(
                        self._get_ws_url(),
                        header={"Authorization": f"Bearer {self.access_token}"},
                        on_open=self.on_open,
                        on_message=self.on_message,
                        on_error=self.on_error,
                        on_close=self.on_close
                    )
                    self.ws.run_forever(sslopt={"cert_reqs": ssl.CERT_NONE})
                except:
                    pass
                
                self.reconnect_attempts += 1
                time.sleep(5)
        
        self.thread = threading.Thread(target=run, daemon=True)
        self.thread.start()

    def get_ltp(self, instrument_key):
        with self.lock:
            return self.data_store.get(instrument_key, {}).get("ltp", 0.0)

    def get_all_data(self):
        with self.lock:
            return self.data_store.copy()
