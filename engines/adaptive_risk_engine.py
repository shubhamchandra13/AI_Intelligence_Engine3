# ============================================================ 
# 🧠 ADAPTIVE RISK ENGINE – INSTITUTIONAL VERSION 5.0
# Regime + Confidence + OI + Theta + IV + AI Hybrid
# + Intelligence-Based Risk Scaling
# Fully Backward Compatible | Main.py Safe
# NOTHING REMOVED – ONLY UPGRADED
# ============================================================

from engines.ai_position_sizing_engine import AIPositionSizingEngine
from engines.equity_curve_engine import EquityCurveEngine


class AdaptiveRiskEngine:

    def __init__(self):
        # 🔥 AI Layer Injected (SAFE)
        self.ai_engine = AIPositionSizingEngine()
        # 🔥 Level 5 Equity Manager (NEW)
        self.equity_manager = EquityCurveEngine()

    def calculate_dynamic_risk(
        self,
        regime,
        confidence=60,
        oi_data=None,
        theta_data=None,
        iv_data=None,  # 🆕 IV Integrated (SAFE DEFAULT)
        base_risk=1.0,
        intelligence_stats=None
    ):

        """
        Institutional Dynamic Risk Engine + AI Hybrid + Intelligence Scaling
        """

        # ================= SAFETY CHECKS =================

        if not isinstance(base_risk, (int, float)):
            base_risk = 1.0

        if not isinstance(regime, dict):
            return round(base_risk, 2)

        regime_name = regime.get("regime", "")
        risk = base_risk

        # ================= REGIME MULTIPLIER =================

        if regime_name == "RANGE_NORMAL_VOL":
            risk *= 0.8

        elif regime_name == "TREND_NORMAL_VOL":
            risk *= 1.2

        elif regime_name == "TREND_HIGH_VOL":
            risk *= 1.5

        elif regime_name == "EXPLOSIVE_VOL":
            risk *= 1.8

        else:
            risk *= 1.0

        # ================= CONFIDENCE SCALING =================

        if confidence >= 80:
            risk *= 1.25

        elif confidence >= 70:
            risk *= 1.10

        elif confidence < 55:
            risk *= 0.7

        # ================= OI BIAS FILTER =================

        if isinstance(oi_data, dict):
            oi_bias = oi_data.get("bias", "NEUTRAL")

            if oi_bias in ["STRONG_BULLISH", "STRONG_BEARISH"]:
                risk *= 1.15

            elif oi_bias == "NEUTRAL":
                risk *= 0.85

        # ================= THETA FILTER =================

        if isinstance(theta_data, dict):
            theta_risk = theta_data.get("theta_risk", "")

            if theta_risk == "HIGH":
                risk *= 0.8

            elif theta_risk == "EXTREME":
                risk *= 0.6

        # ================= IV FILTER (NEW SAFE LAYER) =================

        if isinstance(iv_data, dict):
            iv_regime = iv_data.get("iv_regime") or iv_data.get("regime")

            if iv_regime == "LOW_IV":
                risk *= 1.1

            elif iv_regime == "HIGH_IV":
                risk *= 0.85

            elif iv_regime == "EXTREME_IV":
                risk *= 0.7

        # =====================================================
        # 🔥 AI POSITION SIZING HYBRID LAYER (UPGRADED)
        # =====================================================

        try:
            ai_risk = self.ai_engine.calculate_risk(
                regime=regime,
                confidence=confidence,
                iv_result=iv_data,
                oi_result=oi_data,
                intelligence_report=intelligence_stats,
                base_risk=base_risk
            )

            # Balanced Institutional Blend
            risk = (risk * 0.6) + (ai_risk * 0.4)

        except Exception:
            # Absolute safety fallback
            pass

        # =====================================================
        # 🧠 INTELLIGENCE-BASED SCALING
        # =====================================================

        if isinstance(intelligence_stats, dict) and intelligence_stats:

            win_rate = intelligence_stats.get("win_rate", 0)
            drawdown = intelligence_stats.get("max_drawdown", 0)
            expectancy = intelligence_stats.get("expectancy", 0)

            # ----- Win Rate Scaling -----
            if win_rate > 60:
                risk *= 1.15
            elif win_rate < 45:
                risk *= 0.75

            # ----- Expectancy Scaling -----
            if expectancy > 1:
                risk *= 1.1
            elif expectancy < 0:
                risk *= 0.8

            # ----- Drawdown Protection -----
            if drawdown < -20:
                risk *= 0.4
            elif drawdown < -10:
                risk *= 0.6

        # =====================================================
        # 📈 LEVEL 5 EQUITY CURVE RISK SCALING (NEW)
        # =====================================================
        try:
            equity_multiplier = self.equity_manager.get_equity_risk_multiplier()
            risk *= equity_multiplier
        except Exception:
            pass

        # ================= HARD SAFETY CAP =================

        if risk > 3:
            risk = 3

        if risk < 0.3:
            risk = 0.3

        return round(risk, 2)