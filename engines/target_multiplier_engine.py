# ============================================================
# 🎯 TARGET MULTIPLIER ENGINE – INSTITUTIONAL VERSION 4.0
# Original Logic Preserved + Intelligence + Confidence + IV
# Backward Compatible | Main.py Safe
# ============================================================


class TargetMultiplierEngine:

    def __init__(self):
        pass

    def get_adaptive_multiplier(
        self,
        regime,
        confidence=60,
        intelligence_stats=None,
        iv_data=None
    ):

        # ====================================================
        # 1️⃣ ORIGINAL LOGIC (FULLY PRESERVED – NO TRIM)
        # ====================================================

        multiplier = 1.0  # default fallback

        if isinstance(regime, dict):

            trend = regime.get("trend")
            volatility = regime.get("volatility")

            # Trend + High Vol → Big runner
            if trend in ["UPTREND", "DOWNTREND"] and volatility == "HIGH_VOL":
                multiplier = 3.0

            # Trend + Normal Vol
            elif trend in ["UPTREND", "DOWNTREND"]:
                multiplier = 2.0

            # Range market
            elif trend == "RANGE":
                multiplier = 1.5

            # Low Vol fallback
            else:
                multiplier = 1.0

        # ====================================================
        # 2️⃣ CONFIDENCE BOOST (NEW LAYER)
        # ====================================================

        if confidence >= 85:
            multiplier *= 1.25
        elif confidence >= 75:
            multiplier *= 1.15
        elif confidence < 55:
            multiplier *= 0.8

        # ====================================================
        # 3️⃣ INTELLIGENCE ADJUSTMENT (NEW LAYER)
        # ====================================================

        if intelligence_stats and isinstance(intelligence_stats, dict):

            win_rate = intelligence_stats.get("win_rate", 0)
            drawdown = intelligence_stats.get("max_drawdown", 0)
            expectancy = intelligence_stats.get("expectancy", 0)

            # Win rate boost
            if win_rate > 60:
                multiplier *= 1.2
            elif win_rate < 45:
                multiplier *= 0.75

            # Expectancy boost
            if expectancy > 1:
                multiplier *= 1.15
            elif expectancy < 0:
                multiplier *= 0.7

            # Drawdown compression
            if drawdown < -20:
                multiplier *= 0.5
            elif drawdown < -10:
                multiplier *= 0.7

        # ====================================================
        # 4️⃣ IV REGIME ADJUSTMENT (NEW LAYER)
        # ====================================================

        if iv_data and isinstance(iv_data, dict):

            iv_regime = iv_data.get("regime")

            if iv_regime == "HIGH_IV":
                multiplier *= 0.85   # faster exits
            elif iv_regime == "LOW_IV":
                multiplier *= 1.15   # allow bigger move

        # ====================================================
        # 5️⃣ HARD SAFETY LIMITS
        # ====================================================

        if multiplier > 5:
            multiplier = 5

        if multiplier < 0.8:
            multiplier = 0.8

        return round(multiplier, 2)