# ============================================================
# 🧠 OPTION CHAIN INTELLIGENCE ENGINE (ROBUST VERSION)
# OI Based Smart Money Confirmation Layer
# ============================================================

class OptionChainEngine:

    def analyze_oi(self, option_chain_data):

        """
        Expected format:
        [
            {
                "strike": 25500,
                "call_oi": 120000,
                "put_oi": 90000,
                "call_oi_change": 15000,
                "put_oi_change": -5000
            },
            ...
        ]
        """

        # ================= SAFE CHECK =================

        if not option_chain_data or not isinstance(option_chain_data, list):
            return {
                "bias": "NEUTRAL",
                "pcr": 1.0,
                "call_wall": None,
                "put_wall": None
            }

        # ================= SAFE EXTRACTION =================

        cleaned_data = []

        for item in option_chain_data:

            strike = item.get("strike")
            call_oi = item.get("call_oi", 0)
            put_oi = item.get("put_oi", 0)

            # Skip invalid rows
            if strike is None:
                continue

            cleaned_data.append({
                "strike": strike,
                "call_oi": call_oi,
                "put_oi": put_oi
            })

        if not cleaned_data:
            return {
                "bias": "NEUTRAL",
                "pcr": 1.0,
                "call_wall": None,
                "put_wall": None
            }

        # ================= TOTAL OI =================

        total_call_oi = sum(item["call_oi"] for item in cleaned_data)
        total_put_oi = sum(item["put_oi"] for item in cleaned_data)

        pcr = round(total_put_oi / total_call_oi, 2) if total_call_oi != 0 else 1.0

        # ================= OI WALLS =================

        call_wall = max(cleaned_data, key=lambda x: x["call_oi"])["strike"]
        put_wall = max(cleaned_data, key=lambda x: x["put_oi"])["strike"]

        # ================= BIAS LOGIC =================

        if pcr > 1.2:
            bias = "BULLISH_OI"
        elif pcr < 0.8:
            bias = "BEARISH_OI"
        else:
            bias = "NEUTRAL"

        return {
            "bias": bias,
            "pcr": pcr,
            "call_wall": call_wall,
            "put_wall": put_wall,
            "total_call_oi": total_call_oi,
            "total_put_oi": total_put_oi
        }