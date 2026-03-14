import numpy as np

def detect_fvg(df, liquidity_direction=None, lookback=50):

    if len(df) < lookback:
        return {"status": "No FVG", "strength": 0, "in_zone": False}

    recent = df.iloc[-lookback:]
    avg_range = (recent["high"] - recent["low"]).mean()

    current_price = df["close"].iloc[-1]

    # Reverse loop (latest FVG first)
    for i in range(len(recent) - 3, 2, -1):

        c1 = recent.iloc[i-2]
        c2 = recent.iloc[i-1]
        c3 = recent.iloc[i]

        range_c2 = c2["high"] - c2["low"]

        # Strong displacement filter
        if range_c2 < avg_range * 1.5:
            continue

        # -----------------------------
        # Bearish FVG
        # -----------------------------
        if liquidity_direction == "BEARISH":
            if c1["low"] > c3["high"]:

                zone_high = c1["low"]
                zone_low = c3["high"]

                gap_size = zone_high - zone_low
                strength = min(1, gap_size / avg_range)

                in_zone = zone_low <= current_price <= zone_high

                return {
                    "status": "Bearish FVG",
                    "zone_low": zone_low,
                    "zone_high": zone_high,
                    "strength": round(strength, 2),
                    "in_zone": in_zone
                }

        # -----------------------------
        # Bullish FVG
        # -----------------------------
        if liquidity_direction == "BULLISH":
            if c1["high"] < c3["low"]:

                zone_low = c1["high"]
                zone_high = c3["low"]

                gap_size = zone_high - zone_low
                strength = min(1, gap_size / avg_range)

                in_zone = zone_low <= current_price <= zone_high

                return {
                    "status": "Bullish FVG",
                    "zone_low": zone_low,
                    "zone_high": zone_high,
                    "strength": round(strength, 2),
                    "in_zone": in_zone
                }

    return {"status": "No FVG", "strength": 0, "in_zone": False}