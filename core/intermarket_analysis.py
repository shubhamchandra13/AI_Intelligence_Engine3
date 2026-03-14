import pandas as pd

def detect_smt_divergence(nifty_df, banknifty_df, lookback=5):
    """
    Detects SMT Divergence between Nifty and BankNifty.
    Bullish SMT: One makes Lower Low, other makes Higher Low (Strong Buying)
    Bearish SMT: One makes Higher High, other makes Lower High (Strong Selling)
    """
    if nifty_df is None or banknifty_df is None or len(nifty_df) < lookback or len(banknifty_df) < lookback:
        return {"status": "NEUTRAL", "strength": 0, "reason": "Insufficient Data"}

    # Get recent Highs and Lows
    n_highs = nifty_df['high'].tail(lookback).values
    b_highs = banknifty_df['high'].tail(lookback).values
    n_lows = nifty_df['low'].tail(lookback).values
    b_lows = banknifty_df['low'].tail(lookback).values

    # 1. BEARISH SMT CHECK (At recent Highs)
    n_hh = n_highs[-1] > max(n_highs[:-1])
    b_lh = b_highs[-1] < max(b_highs[:-1])
    
    b_hh = b_highs[-1] > max(b_highs[:-1])
    n_lh = n_highs[-1] < max(n_highs[:-1])

    if (n_hh and b_lh) or (b_hh and n_lh):
        return {
            "status": "BEARISH SMT",
            "strength": 80,
            "reason": "HH/LH Divergence (Institutional Selling)"
        }

    # 2. BULLISH SMT CHECK (At recent Lows)
    n_ll = n_lows[-1] < min(n_lows[:-1])
    b_hl = b_lows[-1] > min(b_lows[:-1])
    
    b_ll = b_lows[-1] < min(b_lows[:-1])
    n_hl = n_lows[-1] > min(n_lows[:-1])

    if (n_ll and b_hl) or (b_ll and n_hl):
        return {
            "status": "BULLISH SMT",
            "strength": 80,
            "reason": "LL/HL Divergence (Institutional Buying)"
        }

    return {"status": "SYNCED", "strength": 0, "reason": "Indices moving together"}
