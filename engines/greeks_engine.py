# ============================================================
# 🧠 GREEKS INTELLIGENCE ENGINE – INSTITUTIONAL VERSION
# Delta Classification + Quality Scoring + Trade Suitability
# ============================================================


class GreeksEngine:

    def __init__(self):
        pass

    # ------------------------------------------------------------
    # 🔹 DELTA CLASSIFICATION
    # ------------------------------------------------------------
    def classify_delta(self, delta_value):

        if delta_value is None:
            return {
                "delta_zone": "UNKNOWN",
                "quality": "LOW",
                "score": 0,
                "tradable": False
            }

        delta_abs = abs(delta_value)

        # 🎯 Optimal Buying Zone
        if 0.45 <= delta_abs <= 0.65:
            return {
                "delta_zone": "OPTIMAL",
                "quality": "HIGH",
                "score": 90,
                "tradable": True
            }

        # Slight OTM (Acceptable)
        elif 0.30 <= delta_abs < 0.45:
            return {
                "delta_zone": "SLIGHT_OTM",
                "quality": "MEDIUM",
                "score": 65,
                "tradable": True
            }

        # Deep ITM (Low RR)
        elif delta_abs > 0.75:
            return {
                "delta_zone": "DEEP_ITM",
                "quality": "LOW",
                "score": 40,
                "tradable": False
            }

        # Far OTM (Lottery)
        else:
            return {
                "delta_zone": "FAR_OTM",
                "quality": "LOW",
                "score": 30,
                "tradable": False
            }

    # ------------------------------------------------------------
    # 🔹 FULL ANALYSIS WRAPPER
    # ------------------------------------------------------------
    def analyze(self, delta_value):

        result = self.classify_delta(delta_value)

        return {
            "delta_value": delta_value,
            "delta_zone": result["delta_zone"],
            "quality": result["quality"],
            "score": result["score"],
            "tradable": result["tradable"]
        }