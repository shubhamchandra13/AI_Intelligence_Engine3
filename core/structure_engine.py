import pandas as pd


def detect_swings(df, lookback=5):

    df = df.copy()
    df["swing_high"] = False
    df["swing_low"] = False

    for i in range(lookback, len(df) - lookback):
        high_range = df["high"].iloc[i - lookback:i + lookback + 1]
        low_range = df["low"].iloc[i - lookback:i + lookback + 1]

        if df["high"].iloc[i] == max(high_range):
            df.at[df.index[i], "swing_high"] = True

        if df["low"].iloc[i] == min(low_range):
            df.at[df.index[i], "swing_low"] = True

    return df


def analyze_structure(df):

    if len(df) < 50:
        return {
            "bias": "Neutral",
            "structure": "Not enough data",
            "bos": False,
            "choch": False
        }

    df = detect_swings(df)

    swing_highs = df[df["swing_high"]]
    swing_lows = df[df["swing_low"]]

    if len(swing_highs) < 2 or len(swing_lows) < 2:
        return {
            "bias": "Neutral",
            "structure": "Not enough swing points",
            "bos": False,
            "choch": False
        }

    last_high = swing_highs["high"].iloc[-1]
    prev_high = swing_highs["high"].iloc[-2]

    last_low = swing_lows["low"].iloc[-1]
    prev_low = swing_lows["low"].iloc[-2]

    current_close = df["close"].iloc[-1]

    bos = False
    choch = False

    # --- MOMENTUM OVERLAY (NEW: REAL-TIME FIX) ---
    momentum_bias = "Neutral"
    short_ma = df["close"].tail(5).mean()
    long_ma = df["close"].tail(20).mean()
    current_price = df["close"].iloc[-1]
    
    # If price is significantly below both MAs, force Bearish momentum
    if current_price < short_ma and short_ma < long_ma:
        momentum_bias = "Bearish"
    elif current_price > short_ma and short_ma > long_ma:
        momentum_bias = "Bullish"

    # Bullish Structure
    if last_high > prev_high and last_low > prev_low:
        bias = "Bullish"
        if momentum_bias == "Bearish": # Override if market is crashing
            bias = "Transition (Bullish but Pullback)"
        structure = "HH-HL Structure"

        if current_close > prev_high:
            bos = True

    # Bearish Structure
    elif last_high < prev_high and last_low < prev_low:
        bias = "Bearish"
        structure = "LH-LL Structure"

        if current_close < prev_low:
            bos = True

    # Transition / Reversal Detection
    else:
        bias = "Transition"
        if momentum_bias == "Bearish": bias = "Bearish (Momentum Break)"
        structure = "Structure Transition"
        choch = True

    # --- SCORE CALCULATION (NEW) ---
    structure_score = 50
    if bias == "Bullish":
        structure_score = 80 if bos else 70
    elif bias == "Bearish":
        structure_score = 80 if bos else 70
    elif bias == "Transition":
        structure_score = 55

    return {
        "bias": bias,
        "structure": structure,
        "bos": bos,
        "choch": choch,
        "structure_score": structure_score
    }