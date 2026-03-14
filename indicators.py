"""
AI Quant Engine - Indicators Module
All technical indicator calculations here
"""

import pandas as pd
import numpy as np
import json
import os

# ==========================================================
# LOAD OPTIMIZED PARAMETERS (AI SELF-LEARNING)
# ==========================================================
_CACHED_PARAMS = None

def _get_param(key, default):
    global _CACHED_PARAMS
    if _CACHED_PARAMS is None:
        try:
            if os.path.exists("database/optimized_params.json"):
                with open("database/optimized_params.json", "r") as f:
                    _CACHED_PARAMS = json.load(f)
            else:
                _CACHED_PARAMS = {}
        except:
            _CACHED_PARAMS = {}
            
    return _CACHED_PARAMS.get(key, default)

# ==========================================================
# SAFE NUMERIC CONVERTER
# ==========================================================

def _to_numeric(series):
    """
    Ensures series is numeric and drops invalid values
    """
    return pd.to_numeric(series, errors="coerce")


# ==========================================================
# EMA
# ==========================================================

def calculate_ema(series, period=None):
    """
    Expects: pandas Series
    Returns: EMA Series
    """
    if period is None:
        period = 9 # Fallback
        
    if series is None or len(series) == 0:
        return pd.Series(dtype=float)

    series = _to_numeric(series)

    return series.ewm(span=period, adjust=False).mean()


# ==========================================================
# VWAP
# ==========================================================

def calculate_vwap(df):
    """
    Requires columns: high, low, close, volume
    Returns VWAP Series
    """

    required_cols = ["high", "low", "close", "volume"]

    for col in required_cols:
        if col not in df.columns:
            return pd.Series(dtype=float)

    typical_price = (df["high"] + df["low"] + df["close"]) / 3
    volume = _to_numeric(df["volume"])

    vwap = (typical_price * volume).cumsum() / volume.cumsum()

    return vwap


# ==========================================================
# ATR (Volatility Base)
# ==========================================================

def calculate_atr(df, period=None):
    """
    Average True Range
    Requires: high, low, close
    """
    if period is None:
        period = _get_param("atr_period", 14)

    required_cols = ["high", "low", "close"]

    for col in required_cols:
        if col not in df.columns:
            return pd.Series(dtype=float)

    high = _to_numeric(df["high"])
    low = _to_numeric(df["low"])
    close = _to_numeric(df["close"])

    prev_close = close.shift(1)

    tr1 = high - low
    tr2 = abs(high - prev_close)
    tr3 = abs(low - prev_close)

    true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

    atr = true_range.rolling(window=period).mean()

    return atr


# ==========================================================
# RSI (Future Institutional Bias Layer)
# ==========================================================

def calculate_rsi(series, period=None):
    """
    Relative Strength Index
    Expects close price Series
    """
    if period is None:
        period = _get_param("rsi_period", 14)

    if series is None or len(series) == 0:
        return pd.Series(dtype=float)

    series = _to_numeric(series)

    delta = series.diff()

    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)

    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()

    rs = avg_gain / avg_loss

    rsi = 100 - (100 / (1 + rs))

    return rsi


# ==========================================================
# BOLLINGER BANDS (Volatility Expansion Detection)
# ==========================================================

def calculate_bollinger(series, period=None, std_dev=2):
    """
    Bollinger Bands
    """
    if period is None:
        period = _get_param("bb_period", 20)

    if series is None or len(series) == 0:
        return pd.Series(dtype=float), pd.Series(dtype=float)

    series = _to_numeric(series)

    sma = series.rolling(window=period).mean()
    std = series.rolling(window=period).std()

    upper = sma + (std_dev * std)
    lower = sma - (std_dev * std)

    return upper, lower


# ==========================================================
# FIBONACCI LEVELS (Dynamic Support/Resistance)
# ==========================================================

def calculate_fibonacci_levels(df, lookback=None):
    """
    Calculates Fibonacci Retracement levels based on recent high/low
    Returns a dict of levels
    """
    if lookback is None:
        lookback = _get_param("fib_lookback", 50)

    if df is None or len(df) < lookback:
        return None

    high = _to_numeric(df["high"]).iloc[-lookback:].max()
    low = _to_numeric(df["low"]).iloc[-lookback:].min()
    diff = high - low

    if diff == 0:
        return None

    levels = {
        "0.0": high,
        "0.236": high - 0.236 * diff,
        "0.382": high - 0.382 * diff,
        "0.5": high - 0.5 * diff,
        "0.618": high - 0.618 * diff,
        "0.786": high - 0.786 * diff,
        "1.0": low
    }
    return levels

def detect_fibonacci_bounce(df, current_price, lookback=None):
    """
    Detects if price is near key Fibonacci levels (Golden Pocket 0.5-0.618)
    """
    if lookback is None:
        lookback = _get_param("fib_lookback", 50)
        
    levels = calculate_fibonacci_levels(df, lookback)
    if not levels:
        return "NONE", 0.0

    cp = float(current_price)
    
    # Check for support bounce near 0.5 and 0.618
    # 1% tolerance for being "near" a level
    tol = (levels["0.0"] - levels["1.0"]) * 0.01 

    if abs(cp - levels["0.618"]) <= tol:
        return "BULLISH_0.618", 1.0
    if abs(cp - levels["0.5"]) <= tol:
        return "BULLISH_0.5", 0.8
    if abs(cp - levels["0.382"]) <= tol:
        return "BULLISH_0.382", 0.5
        
    return "NONE", 0.0


# ==========================================================
# MACD
# ==========================================================

def calculate_macd(series, fast=None, slow=None, signal=None):
    if fast is None: fast = _get_param("macd_fast", 12)
    if slow is None: slow = _get_param("macd_slow", 26)
    if signal is None: signal = _get_param("macd_signal", 9)

    if series is None or len(series) == 0:
        return pd.Series(dtype=float), pd.Series(dtype=float), pd.Series(dtype=float)

    series = _to_numeric(series)
    ema_fast = series.ewm(span=fast, adjust=False).mean()
    ema_slow = series.ewm(span=slow, adjust=False).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    hist = macd_line - signal_line
    return macd_line, signal_line, hist


# ==========================================================
# STOCHASTIC RSI-LIKE MOMENTUM (K/D)
# ==========================================================

def calculate_stochastic(df, k_period=None, d_period=3):
    if k_period is None:
        k_period = _get_param("stoch_k", 14)

    required_cols = ["high", "low", "close"]
    for col in required_cols:
        if col not in df.columns:
            return pd.Series(dtype=float), pd.Series(dtype=float)

    high = _to_numeric(df["high"])
    low = _to_numeric(df["low"])
    close = _to_numeric(df["close"])

    lowest_low = low.rolling(k_period).min()
    highest_high = high.rolling(k_period).max()
    denom = (highest_high - lowest_low).replace(0, np.nan)

    k = ((close - lowest_low) / denom) * 100
    k = k.ffill().fillna(50)
    d = k.rolling(d_period).mean().fillna(50)
    return k, d


# ==========================================================
# SUPERTREND
# ==========================================================

def calculate_supertrend(df, period=None, multiplier=None):
    if period is None: period = _get_param("supertrend_period", 10)
    if multiplier is None: multiplier = _get_param("supertrend_mult", 3)

    required_cols = ["high", "low", "close"]
    for col in required_cols:
        if col not in df.columns:
            return pd.Series(dtype=float), pd.Series(dtype=bool)

    high = _to_numeric(df["high"])
    low = _to_numeric(df["low"])
    close = _to_numeric(df["close"])

    atr = calculate_atr(df, period=period).ffill()
    hl2 = (high + low) / 2.0
    upperband = hl2 + (multiplier * atr)
    lowerband = hl2 - (multiplier * atr)

    final_upper = upperband.copy()
    final_lower = lowerband.copy()
    trend_up = pd.Series(index=df.index, dtype=bool)

    for i in range(len(df)):
        if i == 0:
            trend_up.iloc[i] = True
            continue

        prev = i - 1
        if close.iloc[i] > final_upper.iloc[prev]:
            trend_up.iloc[i] = True
        elif close.iloc[i] < final_lower.iloc[prev]:
            trend_up.iloc[i] = False
        else:
            trend_up.iloc[i] = trend_up.iloc[prev]
            if trend_up.iloc[i] and final_lower.iloc[i] < final_lower.iloc[prev]:
                final_lower.iloc[i] = final_lower.iloc[prev]
            if (not trend_up.iloc[i]) and final_upper.iloc[i] > final_upper.iloc[prev]:
                final_upper.iloc[i] = final_upper.iloc[prev]

        if trend_up.iloc[i]:
            final_upper.iloc[i] = np.nan
        else:
            final_lower.iloc[i] = np.nan

    supertrend_line = pd.Series(index=df.index, dtype=float)
    supertrend_line[trend_up] = final_lower[trend_up]
    supertrend_line[~trend_up] = final_upper[~trend_up]

    return supertrend_line, trend_up


# ==========================================================
# RSI DIVERGENCE (SIMPLE SWING APPROX)
# ==========================================================

def detect_rsi_divergence(df, rsi_period=None, lookback=20):
    if rsi_period is None:
        rsi_period = _get_param("rsi_period", 14)

    if df is None or len(df) < max(lookback + 2, 25) or "close" not in df.columns:
        return "NONE"

    close = _to_numeric(df["close"])
    rsi = calculate_rsi(close, period=rsi_period)

    recent_close = close.iloc[-lookback:]
    recent_rsi = rsi.iloc[-lookback:]

    if recent_close.isna().all() or recent_rsi.isna().all():
        return "NONE"

    price_slope = recent_close.iloc[-1] - recent_close.iloc[0]
    rsi_slope = recent_rsi.iloc[-1] - recent_rsi.iloc[0]

    if price_slope > 0 and rsi_slope < 0:
        return "BEARISH"
    if price_slope < 0 and rsi_slope > 0:
        return "BULLISH"
    return "NONE"


# ==========================================================
# STACK EVALUATOR
# ==========================================================

def evaluate_indicator_stack(df):
    if df is None or len(df) < 60 or "close" not in df.columns:
        return {
            "available": False,
            "score": 50,
            "bias": "NEUTRAL",
            "score_adjustment": 0.0,
            "signals": {},
        }

    close = _to_numeric(df["close"])
    last_close = float(close.iloc[-1])

    # Dynamic Parameters
    p_ema_fast = _get_param("ema_fast", 9)
    p_ema_slow = _get_param("ema_slow", 21)
    
    ema_fast = calculate_ema(close, period=p_ema_fast)
    ema_slow = calculate_ema(close, period=p_ema_slow)
    ema_50 = calculate_ema(close, period=50)
    ema_200 = calculate_ema(close, period=200)
    
    ema_cross_bull = bool(ema_fast.iloc[-1] > ema_slow.iloc[-1])
    ema_trend_bull = bool(last_close > ema_50.iloc[-1] and ema_50.iloc[-1] > ema_200.iloc[-1])

    vwap = calculate_vwap(df)
    vwap_bull = bool(len(vwap) and pd.notna(vwap.iloc[-1]) and last_close > float(vwap.iloc[-1]))

    macd_line, signal_line, macd_hist = calculate_macd(close)
    macd_bull = bool(
        len(macd_line) and len(signal_line)
        and pd.notna(macd_line.iloc[-1]) and pd.notna(signal_line.iloc[-1])
        and macd_line.iloc[-1] > signal_line.iloc[-1]
    )

    stoch_k, stoch_d = calculate_stochastic(df)
    stoch_bull = bool(
        len(stoch_k) and len(stoch_d)
        and pd.notna(stoch_k.iloc[-1]) and pd.notna(stoch_d.iloc[-1])
        and stoch_k.iloc[-1] > stoch_d.iloc[-1]
        and stoch_k.iloc[-1] < 80
    )

    divergence = detect_rsi_divergence(df, rsi_period=14, lookback=20)
    divergence_bull = divergence == "BULLISH"
    divergence_bear = divergence == "BEARISH"

    fib_bias, fib_conf = detect_fibonacci_bounce(df, last_close, lookback=50)
    fib_bull = "BULLISH" in fib_bias

    _, trend_up = calculate_supertrend(df, period=10, multiplier=3)
    supertrend_bull = bool(len(trend_up) and bool(trend_up.iloc[-1]))

    score = 50.0
    score += 7 if ema_cross_bull else -7
    score += 8 if ema_trend_bull else -8
    score += 5 if vwap_bull else -5
    score += 7 if macd_bull else -7
    score += 6 if stoch_bull else -6
    score += 8 if supertrend_bull else -8
    score += (10 * fib_conf) if fib_bull else 0
    
    if divergence_bull:
        score += 8
    elif divergence_bear:
        score -= 8

    score = round(max(0.0, min(100.0, score)), 2)
    if score >= 60:
        bias = "BULLISH"
    elif score <= 40:
        bias = "BEARISH"
    else:
        bias = "NEUTRAL"

    adjustment = round(((score - 50.0) / 50.0) * 6.0, 2)

    return {
        "available": True,
        "score": score,
        "bias": bias,
        "score_adjustment": adjustment,
        "signals": {
            "ema_cross_bull": ema_cross_bull,
            "ema_trend_bull": ema_trend_bull,
            "vwap_bull": vwap_bull,
            "macd_bull": macd_bull,
            "stochastic_bull": stoch_bull,
            "supertrend_bull": supertrend_bull,
            "fib_bias": fib_bias,
            "rsi_divergence": divergence,
            "macd_hist": float(macd_hist.iloc[-1]) if len(macd_hist) and pd.notna(macd_hist.iloc[-1]) else None,
            "stoch_k": float(stoch_k.iloc[-1]) if len(stoch_k) and pd.notna(stoch_k.iloc[-1]) else None,
            "stoch_d": float(stoch_d.iloc[-1]) if len(stoch_d) and pd.notna(stoch_d.iloc[-1]) else None,
            "vwap": float(vwap.iloc[-1]) if len(vwap) and pd.notna(vwap.iloc[-1]) else None,
            "ema9": float(ema_fast.iloc[-1]) if len(ema_fast) and pd.notna(ema_fast.iloc[-1]) else None,
            "ema21": float(ema_slow.iloc[-1]) if len(ema_slow) and pd.notna(ema_slow.iloc[-1]) else None,
            "ema50": float(ema_50.iloc[-1]) if len(ema_50) and pd.notna(ema_50.iloc[-1]) else None,
            "ema200": float(ema_200.iloc[-1]) if len(ema_200) and pd.notna(ema_200.iloc[-1]) else None,
        },
    }


# ==========================================================
# MULTI-TIMEFRAME INDICATOR CONFLUENCE
# ==========================================================

def _ensure_time_index(df):
    if df is None or df.empty:
        return None

    out = df.copy()
    if "timestamp" in out.columns:
        out["timestamp"] = pd.to_datetime(out["timestamp"], errors="coerce")
        out = out.dropna(subset=["timestamp"])
        out = out.set_index("timestamp")
    elif not isinstance(out.index, pd.DatetimeIndex):
        return None

    out = out.sort_index()
    return out


def _resample_ohlcv(df_indexed, rule):
    if df_indexed is None or df_indexed.empty:
        return None

    required_cols = ["open", "high", "low", "close", "volume"]
    for col in required_cols:
        if col not in df_indexed.columns:
            return None

    frame = df_indexed[required_cols].copy()
    rs = frame.resample(rule).agg({
        "open": "first",
        "high": "max",
        "low": "min",
        "close": "last",
        "volume": "sum",
    }).dropna()

    if rs.empty:
        return None

    return rs


def evaluate_mtf_indicator_stack(
    df,
    timeframe_rules=None,
    timeframe_weights=None,
):
    if timeframe_rules is None:
        timeframe_rules = ["1T", "3T", "5T", "15T", "30T"]
    if timeframe_weights is None:
        timeframe_weights = {
            "1T": 0.15,
            "3T": 0.20,
            "5T": 0.25,
            "15T": 0.25,
            "30T": 0.15,
        }

    indexed = _ensure_time_index(df)
    requested = list(timeframe_rules)
    if indexed is None or len(indexed) < 80:
        return {
            "available": False,
            "score": 50.0,
            "bias": "NEUTRAL",
            "score_adjustment": 0.0,
            "confluence": 0.0,
            "active_timeframes": 0,
            "requested_timeframes": requested,
            "missing_timeframes": requested,
            "compatibility_percent": 0.0,
            "timeframes": {},
        }

    tf_results = {}
    missing_timeframes = []
    weighted_sum = 0.0
    total_weight = 0.0
    bullish = 0
    bearish = 0

    for tf in timeframe_rules:
        if tf == "1T":
            tf_df = indexed.copy()
        else:
            tf_df = _resample_ohlcv(indexed, tf)

        if tf_df is None or len(tf_df) < 60:
            missing_timeframes.append(tf)
            continue

        tf_eval = evaluate_indicator_stack(tf_df)
        if not tf_eval.get("available"):
            missing_timeframes.append(tf)
            continue

        weight = float(timeframe_weights.get(tf, 0.0))
        if weight <= 0:
            missing_timeframes.append(tf)
            continue

        tf_results[tf] = tf_eval
        weighted_sum += float(tf_eval.get("score", 50.0)) * weight
        total_weight += weight

        tf_bias = tf_eval.get("bias")
        if tf_bias == "BULLISH":
            bullish += 1
        elif tf_bias == "BEARISH":
            bearish += 1

    if total_weight <= 0:
        return {
            "available": False,
            "score": 50.0,
            "bias": "NEUTRAL",
            "score_adjustment": 0.0,
            "confluence": 0.0,
            "active_timeframes": 0,
            "requested_timeframes": requested,
            "missing_timeframes": requested,
            "compatibility_percent": 0.0,
            "timeframes": {},
        }

    final_score = round(weighted_sum / total_weight, 2)
    if bullish > bearish and bullish > 0:
        final_bias = "BULLISH"
    elif bearish > bullish and bearish > 0:
        final_bias = "BEARISH"
    else:
        final_bias = "NEUTRAL"

    total_votes = bullish + bearish
    confluence = round((max(bullish, bearish) / total_votes) * 100.0, 2) if total_votes else 0.0
    adjustment = round(((final_score - 50.0) / 50.0) * 6.0, 2)
    compatibility_percent = round((len(tf_results) / max(1, len(requested))) * 100.0, 2)

    return {
        "available": True,
        "score": final_score,
        "bias": final_bias,
        "score_adjustment": adjustment,
        "confluence": confluence,
        "active_timeframes": len(tf_results),
        "requested_timeframes": requested,
        "missing_timeframes": missing_timeframes,
        "compatibility_percent": compatibility_percent,
        "timeframes": tf_results,
    }
