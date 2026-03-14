import numpy as np

def detect_liquidity(df, lookback=30, tolerance=0.001):

    if len(df) < lookback:
        return {"status": "No Data", "strength": 0}

    recent = df.iloc[-lookback:]

    highs = recent["high"].values
    lows = recent["low"].values

    current_high = df["high"].iloc[-1]
    current_low = df["low"].iloc[-1]
    current_close = df["close"].iloc[-1]

    equal_high_zone = None
    for i in range(len(highs)-2):
        if abs(highs[i] - highs[i+1]) <= highs[i] * tolerance:
            equal_high_zone = max(highs[i], highs[i+1])

    equal_low_zone = None
    for i in range(len(lows)-2):
        if abs(lows[i] - lows[i+1]) <= lows[i] * tolerance:
            equal_low_zone = min(lows[i], lows[i+1])

    if equal_high_zone:
        if current_high > equal_high_zone and current_close < equal_high_zone:
            strength = min(1, (current_high - equal_high_zone) / equal_high_zone * 50)
            return {
                "status": "Bearish Sweep",
                "zone": equal_high_zone,
                "strength": round(strength, 2)
            }

    if equal_low_zone:
        if current_low < equal_low_zone and current_close > equal_low_zone:
            strength = min(1, (equal_low_zone - current_low) / equal_low_zone * 50)
            return {
                "status": "Bullish Sweep",
                "zone": equal_low_zone,
                "strength": round(strength, 2)
            }

    return {"status": "No Sweep", "strength": 0}