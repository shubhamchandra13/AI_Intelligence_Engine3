# ============================================================
# 🔎 LIVE FUTURES INSTRUMENT RESOLVER – EXCHANGE FORMAT
# ============================================================

from datetime import datetime


class FuturesResolver:

    MONTH_MAP = {
        1: "JAN", 2: "FEB", 3: "MAR", 4: "APR",
        5: "MAY", 6: "JUN", 7: "JUL", 8: "AUG",
        9: "SEP", 10: "OCT", 11: "NOV", 12: "DEC"
    }

    def __init__(self, upstox_client):
        self.client = upstox_client

    def resolve(self, index_symbol, expiry_date):

        try:
            expiry = datetime.strptime(expiry_date, "%Y-%m-%d")

            year_short = str(expiry.year)[-2:]
            month_short = self.MONTH_MAP[expiry.month]

            symbol = index_symbol.upper()

            if symbol == "BANKNIFTY":
                return f"NSE_FO|BANKNIFTY{year_short}{month_short}FUT"

            elif symbol == "NIFTY":
                return f"NSE_FO|NIFTY{year_short}{month_short}FUT"

            else:
                return None

        except Exception:
            return None