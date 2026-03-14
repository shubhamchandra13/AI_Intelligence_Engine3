# ============================================================
# ⏳ THETA INTELLIGENCE ENGINE
# Time Decay Risk Analyzer for Option Buying
# ============================================================

from datetime import datetime


class ThetaEngine:

    def __init__(self):

        pass

    # ------------------------------------------------------------
    # Calculate Days to Expiry
    # ------------------------------------------------------------
    def days_to_expiry(self, expiry_date):

        today = datetime.now().date()
        expiry = expiry_date.date()

        return (expiry - today).days

    # ------------------------------------------------------------
    # Analyze Theta Risk
    # ------------------------------------------------------------
    def analyze_theta(self, expiry_date, option_premium):

        dte = self.days_to_expiry(expiry_date)

        if dte <= 0:
            return {
                "theta_risk": "EXPIRED",
                "decay_zone": "HIGH"
            }

        # Rough decay estimation logic
        estimated_daily_decay = option_premium * 0.03  # 3% approx daily decay

        # Risk zones
        if dte <= 2:
            theta_risk = "EXTREME"
            decay_zone = "HIGH"

        elif dte <= 5:
            theta_risk = "HIGH"
            decay_zone = "MEDIUM"

        elif dte <= 10:
            theta_risk = "MODERATE"
            decay_zone = "LOW"

        else:
            theta_risk = "LOW"
            decay_zone = "SAFE"

        return {
            "theta_risk": theta_risk,
            "decay_zone": decay_zone,
            "days_to_expiry": dte,
            "estimated_daily_decay": round(estimated_daily_decay, 2)
        }