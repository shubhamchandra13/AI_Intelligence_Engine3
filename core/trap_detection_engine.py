import pandas as pd
import numpy as np

class TrapDetectionEngine:
    """
    Identifies 'Retail Traps' (Liquidity Sweeps) and Institutional SL hunting.
    """
    def detect_trap(self, df, lookback=20):
        if df is None or len(df) < lookback:
            return {"status": "NONE", "score": 0, "type": "STABLE"}

        try:
            recent = df.tail(lookback).copy()
            highs = recent['high'].max()
            lows = recent['low'].min()
            
            latest = df.iloc[-1]
            prev = df.iloc[-2]

            # 1. Bullish Trap (Short Squeeze / Bear Trap)
            # Price breaks recent low but immediately rejects (wick)
            is_bear_trap = (latest['low'] < lows * 0.9998) and (latest['close'] > lows)
            
            # 2. Bearish Trap (Long Squeeze / Bull Trap)
            # Price breaks recent high but immediately rejects
            is_bull_trap = (latest['high'] > highs * 1.0002) and (latest['close'] < highs)

            # 3. Wick Rejection (Supply/Demand Zone Trap)
            # Large wick compared to body
            body_size = abs(latest['close'] - latest['open'])
            wick_size = (latest['high'] - latest['low']) - body_size
            is_heavy_wick = wick_size > (body_size * 2) and (body_size > 0)

            if is_bear_trap:
                return {"status": "TRAP_DETECTED", "score": 85, "type": "BEAR_TRAP (Buy Institutional)"}
            if is_bull_trap:
                return {"status": "TRAP_DETECTED", "score": 85, "type": "BULL_TRAP (Sell Institutional)"}
            
            if is_heavy_wick:
                return {"status": "REJECTION", "score": 60, "type": "SUPPLY_DEMAND_TRAP"}

            return {"status": "NONE", "score": 0, "type": "MARKET_SYNCED"}
        except:
            return {"status": "NONE", "score": 0, "type": "STABLE"}
