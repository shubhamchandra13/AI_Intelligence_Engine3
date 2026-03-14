# ============================================
# Volatility Expansion Engine
# ============================================

import pandas as pd


def detect_volatility_expansion(df):

    if df is None or len(df) < 50:
        return {
            "expansion": False,
            "strength": "LOW",
            "volatility_score": 30  # <-- ADD SAFE DEFAULT
        }

    # Calculate candle range
    df["range"] = df["high"] - df["low"]

    recent_range = df["range"].tail(5).mean()
    previous_range = df["range"].tail(20).mean()

    # ============================================================
    # ===== ADD BELOW THIS LINE (Volatility Score Overlay)
    # ============================================================

    ratio = recent_range / previous_range if previous_range != 0 else 1

    if ratio > 1.5:
        volatility_score = 90
    elif ratio > 1.2:
        volatility_score = 60
    else:
        volatility_score = 30

    # ATR-style comparison (ORIGINAL LOGIC UNTOUCHED)

    if recent_range > previous_range * 1.5:
        return {
            "expansion": True,
            "strength": "HIGH",
            "volatility_score": volatility_score  # <-- ADD ONLY
        }

    if recent_range > previous_range * 1.2:
        return {
            "expansion": True,
            "strength": "MODERATE",
            "volatility_score": volatility_score  # <-- ADD ONLY
        }

    return {
        "expansion": False,
        "strength": "LOW",
        "volatility_score": volatility_score  # <-- ADD ONLY
    }