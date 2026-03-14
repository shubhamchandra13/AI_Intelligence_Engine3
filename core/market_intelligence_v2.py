import numpy as np
import pandas as pd

class MarketIntelligenceV2:
    """
    Combines Order Flow, Correlation, and Volatility Clustering.
    Detects 'Option Seller' vs 'Option Buyer' market modes.
    """
    def __init__(self):
        self.last_price = None

    def analyze_market_mode(self, df, other_df=None):
        if df is None or len(df) < 50:
            return {"mode": "SCANNING", "reason": "Wait for data..."}

        try:
            # 1. Volatility Clustering (ATR-based)
            tr = df['high'] - df['low']
            atr = tr.rolling(14).mean()
            avg_atr = atr.rolling(50).mean()
            current_atr = atr.iloc[-1]
            
            # 2. Price Range (Bollinger Band Squeeze)
            ma20 = df['close'].rolling(20).mean()
            std20 = df['close'].rolling(20).std()
            bandwidth = (std20 * 4) / ma20 # Width of bands
            current_bandwidth = bandwidth.iloc[-1]

            # 3. Correlation (Nifty vs BankNifty Sync)
            correlation = 1.0
            if other_df is not None:
                common_len = min(len(df), len(other_df), 30)
                correlation = df['close'].tail(common_len).corr(other_df['close'].tail(common_len))

            # --- 🔥 DECISION LOGIC: SELLER VS BUYER MODE ---
            # Seller Mode: Low ATR, Narrow Bandwidth, Ranging price
            if current_atr < (avg_atr.iloc[-1] * 0.8) and current_bandwidth < 0.002:
                return {
                    "mode": "OPTION_SELLER_DOMINATED",
                    "type": "SIDEWAYS_STABLE",
                    "reason": "Low ATR & Squeezed Bands (Theta Decay High)",
                    "action": "AVOID_BUYING / SCALPING_ONLY",
                    "color": "yellow",
                    "sync": round(correlation, 2)
                }
            
            # Buyer Mode: High ATR, Expanding Bands, High Momentum
            if current_atr > (avg_atr.iloc[-1] * 1.2) or current_bandwidth > 0.005:
                direction = "BULLISH" if df['close'].iloc[-1] > ma20.iloc[-1] else "BEARISH"
                return {
                    "mode": "OPTION_BUYER_ACTIVE",
                    "type": f"TRENDING_{direction}",
                    "reason": "Volatility Expansion & High Momentum Detected",
                    "action": f"BUY_{'CE' if direction == 'BULLISH' else 'PE'}_ON_DIPS",
                    "color": "green",
                    "sync": round(correlation, 2)
                }

            return {
                "mode": "NORMAL_TRADING",
                "type": "TRANSITION",
                "reason": "Balanced Market - Waiting for breakout",
                "action": "TRADE_SETUPS_ONLY",
                "color": "cyan",
                "sync": round(correlation, 2)
            }
        except:
            return {"mode": "SCANNING", "reason": "Calculation error"}

    def detect_sudden_change(self, df):
        """Detects rapid shifts in price/volume and provides reasoning."""
        if len(df) < 5: return None
        
        latest = df.iloc[-1]
        prev = df.iloc[-2]
        
        price_change = ((latest['close'] / prev['close']) - 1) * 100
        vol_change = (latest['volume'] / df['volume'].tail(10).mean()) if 'volume' in df else 1.0

        if abs(price_change) > 0.15: # 0.15% in 1 minute is big for index
            reason = "Institutional Block Order" if vol_change > 2.0 else "Stop-Loss Hunting"
            direction = "CRASH" if price_change < 0 else "SPIKE"
            return f"🚨 SUDDEN {direction}: {round(price_change,2)}% move! Reason: {reason}"
            
        return None
