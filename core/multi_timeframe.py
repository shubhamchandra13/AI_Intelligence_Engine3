import pandas as pd
from indicators import calculate_ema


# ============================================
# Resample + EMA Trend
# ============================================

def resample_with_trend(df, timeframe):

    if df is None or len(df) < 150:
        return None

    resampled = df.resample(timeframe).agg({
        "open": "first",
        "high": "max",
        "low": "min",
        "close": "last",
        "volume": "sum"
    }).dropna()

    if len(resampled) < 50:
        return None

    resampled["EMA9"] = calculate_ema(resampled["close"], 9)
    resampled["EMA21"] = calculate_ema(resampled["close"], 21)

    resampled["trend"] = "NEUTRAL"
    resampled.loc[resampled["EMA9"] > resampled["EMA21"], "trend"] = "BULLISH"
    resampled.loc[resampled["EMA9"] < resampled["EMA21"], "trend"] = "BEARISH"

    # Trend strength via slope
    resampled["ema_slope"] = resampled["EMA21"].diff()

    return resampled


# ============================================
# Institutional MTF Bias Engine
# ============================================

def get_multi_timeframe_bias(df):

    if df is None:
        return {
            "label": "NEUTRAL",
            "score": 0
        }

    df_15m = resample_with_trend(df, "15T")
    df_1h = resample_with_trend(df, "1H")
    df_4h = resample_with_trend(df, "4H")

    if df_15m is None or df_1h is None:
        return {
            "label": "NEUTRAL",
            "score": 0
        }

    trend_15m = df_15m["trend"].iloc[-1]
    trend_1h = df_1h["trend"].iloc[-1]

    slope_1h = df_1h["ema_slope"].iloc[-1]

    trend_4h = None
    if df_4h is not None:
        trend_4h = df_4h["trend"].iloc[-1]

    # ---------------------------------------
    # Institutional Alignment Logic
    # (ORIGINAL LOGIC UNTOUCHED)
    # ---------------------------------------

    label = "NEUTRAL"

    # Perfect strong alignment
    if trend_15m == trend_1h and trend_1h == trend_4h:
        label = f"STRONG {trend_1h}"

    # 1H + 15m alignment (primary confirmation)
    elif trend_15m == trend_1h and trend_1h != "NEUTRAL":
        label = trend_1h

    # 1H dominance
    elif trend_1h != "NEUTRAL":
        if slope_1h > 0:
            label = "BULLISH"
        elif slope_1h < 0:
            label = "BEARISH"

    # ============================================================
    # ===== ADD BELOW THIS LINE (Alignment Score Overlay)
    # ============================================================

    trends = [trend_15m, trend_1h]

    if trend_4h:
        trends.append(trend_4h)

    bullish_count = trends.count("BULLISH")
    bearish_count = trends.count("BEARISH")

    alignment_score = max(bullish_count, bearish_count) / len(trends) * 100

    # ============================================================
    # FINAL RETURN (WRAPPED, ORIGINAL LABEL PRESERVED)
    # ============================================================

    return {
        "label": label,
        "score": round(alignment_score, 2)
    }