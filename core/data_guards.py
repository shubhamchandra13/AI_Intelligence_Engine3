# ============================================================
# 🛡️ DATA QUALITY GUARDS
# Audit Item #8: Prevent trading on stale or corrupt data
# ============================================================

import time
import pandas as pd

class DataGuards:
    @staticmethod
    def validate_candles(df, symbol):
        """Checks if candle data is sufficient and fresh."""
        if df is None or df.empty:
            return False, f"Empty dataset for {symbol}"
        
        if len(df) < 50:
            return False, f"Insufficient history for {symbol} ({len(df)} candles)"
        
        # --- 🔥 Level 8: Market Time Logic ---
        import pytz
        from datetime import datetime, time
        IST = pytz.timezone("Asia/Kolkata")
        now_ist = datetime.now(IST)
        curr_time = now_ist.time()
        
        # Define key market times
        pre_market_start = time(9, 0)
        market_open = time(9, 15)
        live_market_stable = time(9, 18)  # Give 3 mins for first candles to stabilize
        market_close = time(15, 30)
        
        last_ts = df.index[-1]
        if last_ts.tzinfo is None:
            last_ts = IST.localize(last_ts)
        
        diff_mins = (now_ist - last_ts).total_seconds() / 60
        
        # Dynamic Threshold Logic
        if pre_market_start <= curr_time < live_market_stable:
            # 9:00 AM to 9:18 AM: Allow yesterday's data (up to 24 hours)
            threshold = 1440 
        elif live_market_stable <= curr_time <= market_close:
            # 9:18 AM to 3:30 PM: Strict live data check (5 mins)
            threshold = 5
        else:
            # Outside market hours: Be slightly relaxed but still alert (30 mins)
            threshold = 30
        
        if diff_mins > threshold:
            return False, f"STALE DATA: {symbol} last update {round(diff_mins, 1)} mins ago"
        
        return True, "OK"

    @staticmethod
    def validate_option_data(premium, iv_data):
        """Checks if option premiums and IV are realistic."""
        if premium is None or premium <= 0:
            return False, "Invalid Option Premium (Zero or None)"
        
        iv = iv_data.get("current_iv", 0)
        if iv <= 0:
            return False, "DATA ERROR: Implied Volatility (IV) is Zero"
        
        if iv > 150: # Extreme outlier check
            return False, f"EXTREME VOLATILITY: IV is {round(iv,1)}% (Likely Data Error)"
            
        return True, "OK"

    @staticmethod
    def validate_spot(spot, symbol):
        """Checks if spot price is valid."""
        if spot is None or spot <= 0:
            return False, f"Invalid Spot Price for {symbol}"
        return True, "OK"
