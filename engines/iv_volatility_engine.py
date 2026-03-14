# ============================================================
# 🌪 IV & VOLATILITY INTELLIGENCE ENGINE – INSTITUTIONAL VERSION++
# Rolling IV Rank + Percentile + Regime + Momentum + Scoring
# ============================================================

import numpy as np


class IVVolatilityEngine:

    def __init__(self, window=100):
        # Rolling IV storage
        self.iv_history = []
        self.window = window

    # ------------------------------------------------------------
    # 🔹 IV ANALYSIS
    # ------------------------------------------------------------
    def analyze(self, iv_data):

        """
        iv_data expected:
        {
            "current_iv": 18.5
        }
        """

        # ---------------- SAFETY CHECK ----------------
        if not iv_data or "current_iv" not in iv_data:
            return {
                "iv_regime": "NORMAL_IV",
                "iv_signal": "NEUTRAL",
                "iv_score": 0,
                "tradable": False,
                "percentile": None,
                "iv_rank": None
            }

        current_iv = iv_data["current_iv"]

        # ---------------- STORE HISTORY ----------------
        self.iv_history.append(current_iv)

        if len(self.iv_history) > self.window:
            self.iv_history.pop(0)

        iv_min = min(self.iv_history)
        iv_max = max(self.iv_history)

        # ---------------- IV RANK ----------------
        if iv_max == iv_min:
            iv_rank = 50
        else:
            iv_rank = ((current_iv - iv_min) / (iv_max - iv_min)) * 100

        # ---------------- PERCENTILE ----------------
        below = [x for x in self.iv_history if x < current_iv]
        percentile = (len(below) / len(self.iv_history)) * 100

        # ---------------- REGIME DETECTION ----------------
        if iv_rank < 30:
            iv_regime = "LOW_IV"
        elif iv_rank > 70:
            iv_regime = "HIGH_IV"
        else:
            iv_regime = "NORMAL_IV"

        # ---------------- MOMENTUM (EXPANSION / CONTRACTION) ----------------
        if len(self.iv_history) > 5:
            if current_iv > self.iv_history[-5]:
                iv_signal = "EXPANDING"
            elif current_iv < self.iv_history[-5]:
                iv_signal = "CONTRACTING"
            else:
                iv_signal = "STABLE"
        else:
            iv_signal = "STABLE"

        # ---------------- SCORING LOGIC ----------------
        iv_score = 50  # neutral base

        # LOW IV bonus (buying friendly)
        if iv_regime == "LOW_IV":
            iv_score += 20

        # Expanding IV bonus (breakout support)
        if iv_signal == "EXPANDING":
            iv_score += 15

        # Deep low percentile bonus
        if percentile < 30:
            iv_score += 15

        # Extreme high IV penalty
        if iv_regime == "HIGH_IV" and percentile > 80:
            iv_score -= 25

        # Clamp score
        iv_score = max(0, min(iv_score, 100))

        # ---------------- TRADE SUITABILITY ----------------
        tradable = True

        # Avoid extreme IV top
        if iv_regime == "HIGH_IV" and percentile > 85:
            tradable = False

        return {
            "iv_regime": iv_regime,
            "iv_signal": iv_signal,
            "iv_score": round(iv_score, 2),
            "percentile": round(percentile, 2),
            "iv_rank": round(iv_rank, 2),
            "current_iv": round(current_iv, 2),
            "tradable": tradable
        }