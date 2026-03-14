# ============================================================
# 🎯 STRIKE SELECTION ENGINE – INSTITUTIONAL VERSION 3.0
# ATM / OTM / ITM + Confidence + OI + IV + Theta + Regime Aware
# Backward Compatible – Nothing Removed – Only Enhanced
# ============================================================

class StrikeSelectionEngine:

    def __init__(self):
        pass

    # ------------------------------------------------------------
    # Auto Step Size Detection
    # ------------------------------------------------------------
    def get_step(self, index):

        if index.upper() == "BANKNIFTY":
            return 100
        elif index.upper() == "NIFTY":
            return 50
        else:
            return 50  # fallback

    # ------------------------------------------------------------
    # Round to nearest ATM strike
    # ------------------------------------------------------------
    def get_atm_strike(self, spot, step):

        remainder = spot % step

        if remainder >= step / 2:
            return int(spot - remainder + step)
        else:
            return int(spot - remainder)

    # ------------------------------------------------------------
    # MAIN STRIKE LOGIC – FULLY UPGRADED
    # ------------------------------------------------------------
    def select_strike(
        self,
        index,
        spot,
        direction,
        regime,
        confidence=60,
        oi_data=None,
        iv_data=None,
        theta_data=None
    ):

        # --------------------------------------------------------
        # Safety Checks
        # --------------------------------------------------------
        if not spot or not direction or not regime:
            return None

        direction = direction.upper()

        step = self.get_step(index)
        atm = self.get_atm_strike(spot, step)

        trend = regime.get("trend", "")
        volatility = regime.get("volatility", "")
        regime_name = regime.get("regime", "")

        option_type = "CE" if direction == "BULLISH" else "PE"

        strike = atm
        moneyness = "ATM"

        # --------------------------------------------------------
        # IV & Theta Awareness (NEW)
        # --------------------------------------------------------
        iv_regime = (iv_data or {}).get("iv_regime", "NORMAL")
        theta_risk = (theta_data or {}).get("theta_risk", "LOW")

        # --------------------------------------------------------
        # HIGH VOLATILITY LOGIC
        # --------------------------------------------------------
        if volatility == "HIGH_VOL":

            if direction == "BULLISH":
                strike = atm + step
            else:
                strike = atm - step

            moneyness = "High Vol OTM"

        # --------------------------------------------------------
        # STRONG TREND + HIGH CONFIDENCE
        # --------------------------------------------------------
        if "TREND" in trend and confidence >= 80:

            if direction == "BULLISH":
                strike = atm + step
            else:
                strike = atm - step

            moneyness = "Trend OTM"

        # --------------------------------------------------------
        # LOW CONFIDENCE → Slight ITM (Safety Mode)
        # --------------------------------------------------------
        if confidence < 55:

            if direction == "BULLISH":
                strike = atm - step
            else:
                strike = atm + step

            moneyness = "Slight ITM"

        # --------------------------------------------------------
        # IV LOW + TREND → Slight OTM Aggression
        # --------------------------------------------------------
        if iv_regime == "LOW" and confidence >= 70 and "TREND" in trend:

            if direction == "BULLISH":
                strike = strike + step
            else:
                strike = strike - step

            moneyness = "Low IV Expansion"

        # --------------------------------------------------------
        # Theta Risk HIGH → Stay ATM
        # --------------------------------------------------------
        if theta_risk in ["HIGH", "EXTREME"]:
            strike = atm
            moneyness = "Theta Safe ATM"

        # --------------------------------------------------------
        # OI Bias Confirmation
        # --------------------------------------------------------
        if isinstance(oi_data, dict):

            oi_bias = oi_data.get("bias", "NEUTRAL")

            if (
                direction == "BULLISH"
                and "BULLISH" in oi_bias
            ):
                moneyness = "OI Confirmed Bullish"

            elif (
                direction == "BEARISH"
                and "BEARISH" in oi_bias
            ):
                moneyness = "OI Confirmed Bearish"

        # --------------------------------------------------------
        # FINAL RETURN (Backward Compatible + Enhanced Fields)
        # --------------------------------------------------------
        return {
            "index": index,
            "spot": spot,
            "atm": atm,
            "strike": strike,
            "option_type": option_type,
            "moneyness": moneyness,
            "confidence": confidence,
            "volatility": volatility,

            # NEW INTELLIGENCE FIELDS
            "regime": regime_name,
            "iv_regime": iv_regime,
            "theta_risk": theta_risk,
            "oi_bias": (oi_data or {}).get("bias", "NEUTRAL")
        }

    def get_ladder_strikes(self, index, spot, direction, confidence, iv_data=None):
        """
        Generates a list of (strike, type, key, weight) for laddered entry.
        Default: 40% ATM, 30% OTM1, 30% ITM1 for balanced risk.
        """
        step = self.get_step(index)
        atm = self.get_atm_strike(spot, step)
        opt_type = "CE" if direction.upper() == "BULLISH" else "PE"

        # High Confidence -> Aggressive Ladder (More OTM)
        if confidence >= 80:
            return [
                (atm, opt_type, None, 0.4),
                (atm + (step if opt_type == "CE" else -step), opt_type, None, 0.4),
                (atm + (2*step if opt_type == "CE" else -2*step), opt_type, None, 0.2)
            ]

        # Low Confidence / High IV -> Conservative Ladder (More ITM)
        return [
            (atm, opt_type, None, 0.4),
            (atm - (step if opt_type == "CE" else -step), opt_type, None, 0.4),
            (atm + (step if opt_type == "CE" else -step), opt_type, None, 0.2)
        ]
