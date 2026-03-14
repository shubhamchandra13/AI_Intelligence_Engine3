"""
Phase 8 – Dual Mode Institutional Engine
"""

def score_intraday(tf_data):
    score = 0

    for tf, data in tf_data.items():

        bias = data["bias"]
        structure = data["structure"]
        liquidity = data["liquidity"]

        if bias == "Bullish":
            score += 8
        else:
            score -= 8

        if "Bullish" in structure:
            score += 6
        if "Bearish" in structure:
            score -= 6

        if "Sweep" in liquidity:
            score += 4

    return max(0, min(100, 50 + score))


def score_swing(tf_data, atr_strength):

    score = 0

    for tf, data in tf_data.items():

        bias = data["bias"]
        structure = data["structure"]
        intent = data["intent"]

        if bias == "Bullish":
            score += 10
        else:
            score -= 10

        if "Bullish" in structure:
            score += 8
        if "Bearish" in structure:
            score -= 8

        if "Bullish" in intent:
            score += 6

    # ATR weight
    score += atr_strength

    return max(0, min(100, 50 + score))


def resolve_conflict(intraday_score, swing_score):

    if intraday_score >= 70 and swing_score >= 70:
        return "Trade + Swing Hold Allowed"

    if intraday_score >= 70 and 50 <= swing_score < 70:
        return "Intraday Only – Do Not Hold"

    if intraday_score >= 70 and swing_score < 50:
        return "Scalp Only – Exit Same Day"

    if intraday_score < 60 and swing_score >= 70:
        return "Wait for Pullback – Swing Dominant"

    return "No Trade – Weak Alignment"