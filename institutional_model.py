def detect_institutional_intent(bias, structure, liquidity):
    """
    Combine bias + structure + liquidity
    Return institutional intent
    """

    # === Bearish Continuation Setup ===
    if (
        bias == "Bearish"
        and "Bearish Structure" in structure
        and liquidity == "Bullish Liquidity Sweep"
    ):
        return "🔥 Bearish Continuation After Bull Trap"

    # === Bullish Continuation Setup ===
    if (
        bias == "Bullish"
        and "Bullish Structure" in structure
        and liquidity == "Bearish Liquidity Sweep"
    ):
        return "🔥 Bullish Continuation After Bear Trap"

    # === Reversal Possibility ===
    if (
        bias == "Bullish"
        and "Bearish Structure" in structure
        and liquidity == "Bullish Liquidity Sweep"
    ):
        return "⚠ Possible Bullish Reversal"

    if (
        bias == "Bearish"
        and "Bullish Structure" in structure
        and liquidity == "Bearish Liquidity Sweep"
    ):
        return "⚠ Possible Bearish Reversal"

    # === Transition Zone ===
    if "Transition" in structure:
        return "⏳ Structure Transition – Wait"

    return "😐 No Clear Institutional Intent"