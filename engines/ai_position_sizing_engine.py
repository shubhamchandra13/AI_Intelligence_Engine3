# ============================================================
# 🧠 AI POSITION SIZING ENGINE – SAFE INTEGRATION VERSION
# Backward Compatible | Crash Protected
# ============================================================

class AIPositionSizingEngine:

    def calculate_risk(
        self,
        regime=None,
        confidence=60,
        iv_result=None,
        oi_result=None,
        intelligence_report=None,
        base_risk=1.0
    ):

        # ------------------------------------------------
        # SAFE DEFAULTS (No Crash Guarantee)
        # ------------------------------------------------
        regime = regime or {"regime": "RANGE_NORMAL_VOL"}
        iv_result = iv_result or {"iv_regime": "NORMAL_IV"}
        oi_result = oi_result or {"bias": "NEUTRAL"}

        # ------------------------------------------------
        # 1️⃣ Base Risk by Regime
        # ------------------------------------------------
        regime_name = regime.get("regime", "RANGE_NORMAL_VOL")

        if "EXPLOSIVE" in regime_name:
            risk = 2.2
        elif "HIGH_VOL" in regime_name:
            risk = 1.8
        elif "TREND" in regime_name:
            risk = 1.2
        else:
            risk = 0.8

        # ------------------------------------------------
        # 2️⃣ Confidence Multiplier
        # ------------------------------------------------
        if confidence < 70:
            risk *= 0.6
        elif 70 <= confidence < 75:
            risk *= 1.0
        elif 75 <= confidence < 85:
            risk *= 1.2
        else:
            risk *= 1.4

        # ------------------------------------------------
        # 3️⃣ IV Adjustment
        # ------------------------------------------------
        iv_regime = iv_result.get("iv_regime", "NORMAL_IV")

        if iv_regime == "LOW_IV":
            risk *= 1.2
        elif iv_regime == "HIGH_IV":
            risk *= 0.8

        # ------------------------------------------------
        # 4️⃣ OI Bias Adjustment
        # ------------------------------------------------
        oi_bias = oi_result.get("bias", "NEUTRAL")

        if oi_bias in ["BULLISH_OI", "BEARISH_OI"]:
            risk += 0.2
        else:
            risk -= 0.1

        # ------------------------------------------------
        # 5️⃣ Performance Adjustment
        # ------------------------------------------------
        if intelligence_report:
            win_rate = intelligence_report.get("win_rate", 50)
            drawdown = intelligence_report.get("max_drawdown", 0)

            if win_rate > 60:
                risk *= 1.2
            elif win_rate < 40:
                risk *= 0.7

            if abs(drawdown) > 10:
                risk = 0.5

        # ------------------------------------------------
        # 6️⃣ Base Risk Blending (Future Ready)
        # ------------------------------------------------
        risk = (risk + base_risk) / 2

        # ------------------------------------------------
        # 7️⃣ Clamp Protection
        # ------------------------------------------------
        risk = max(0.5, min(risk, 3.0))

        return round(risk, 2)