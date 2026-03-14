# ============================================
# Institutional Entry Trigger Engine
# ============================================

def evaluate_entry(structure, mtf_bias, intraday_score, momentum):

    bias = structure["bias"]
    bos = structure["bos"]

    # ===============================
    # Bullish Setup
    # ===============================
    if (
        bias == "Bullish"
        and bos
        and mtf_bias == "Bullish"
        and momentum > 0
        and intraday_score >= 80
    ):
        return {
            "trade": True,
            "direction": "LONG",
            "mode": "AGGRESSIVE"
        }

    # ===============================
    # Bearish Setup
    # ===============================
    if (
        bias == "Bearish"
        and bos
        and mtf_bias == "Bearish"
        and momentum < 0
        and intraday_score >= 80
    ):
        return {
            "trade": True,
            "direction": "SHORT",
            "mode": "AGGRESSIVE"
        }

    # ===============================
    # Moderate Setup
    # ===============================
    if (
        bias in ["Bullish", "Bearish"]
        and bos
        and intraday_score >= 80
    ):
        return {
            "trade": True,
            "direction": bias.upper(),
            "mode": "MODERATE"
        }

    return {
        "trade": False,
        "direction": None,
        "mode": "WAIT"
    }