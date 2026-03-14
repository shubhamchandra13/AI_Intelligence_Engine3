# ============================================================
# 🌍 GLOBAL INTER-ASSET CORRELATION ENGINE (THE MACRO EYE)
# Level 11: Cross-Asset Intelligence Filter
# ============================================================

import yfinance as yf
import pandas as pd
from datetime import datetime

class InterAssetEngine:
    def __init__(self):
        # Tickers for global assets relevant to Nifty
        self.tickers = {
            "Nasdaq": "^IXIC",
            "USDINR": "INR=X",
            "CrudeOil": "BZ=F",
            "Gold": "GC=F",
            "Bitcoin": "BTC-USD"
        }
        self.last_results = {}

    def fetch_macro_data(self):
        """Fetches latest prices and returns for global assets."""
        results = {}
        try:
            for name, ticker in self.tickers.items():
                data = yf.download(ticker, period="2d", interval="1h", progress=False)
                if not data.empty:
                    current_price = data["Close"].iloc[-1]
                    prev_close = data["Close"].iloc[0]
                    change_pct = ((current_price - prev_close) / prev_close) * 100
                    results[name] = {
                        "price": round(float(current_price), 2),
                        "change": round(float(change_pct), 2)
                    }
            self.last_results = results
            return results
        except Exception as e:
            print(f"⚠️ Macro Eye Error: {e}")
            return {}

    def calculate_macro_bias(self):
        """
        Calculates a bias score (-100 to +100) based on global correlations.
        - USDINR up -> Negative for Nifty
        - Crude Oil up -> Negative for Nifty (Inflation)
        - Nasdaq up -> Positive for Nifty (Tech flow)
        - Gold up -> Neutral/Negative (Fear gauge)
        - Bitcoin up -> Positive (Risk-on sentiment)
        """
        if not self.last_results:
            self.fetch_macro_data()
        
        data = self.last_results
        score = 0
        
        # Nasdaq alignment (+20 max)
        if "Nasdaq" in data:
            score += data["Nasdaq"]["change"] * 10 
            
        # USDINR inverse correlation (-30 max)
        if "USDINR" in data:
            score -= data["USDINR"]["change"] * 25
            
        # Crude Oil pressure (-20 max)
        if "CrudeOil" in data:
            score -= data["CrudeOil"]["change"] * 15
            
        # Bitcoin risk-on sentiment (+15 max)
        if "Bitcoin" in data:
            score += data["Bitcoin"]["change"] * 5

        # Gold fear gauge (-15 max)
        if "Gold" in data:
            if data["Gold"]["change"] > 0.5: # Only if significant fear
                score -= 10

        # Normalize score between -100 and 100
        final_score = max(-100, min(100, score))
        
        bias = "NEUTRAL"
        if final_score > 15: bias = "GLOBAL_BULLISH"
        elif final_score < -15: bias = "GLOBAL_BEARISH"
        
        return {
            "macro_score": round(final_score, 2),
            "macro_bias": bias,
            "details": data
        }

if __name__ == "__main__":
    engine = InterAssetEngine()
    print(engine.calculate_macro_bias())
