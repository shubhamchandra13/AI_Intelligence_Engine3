"""
Phase 9 – Hybrid Institutional Relative Strength Engine
Rotation + Directional Mode
Optimized for F&O Trading
"""


# ==========================================
# 🔹 Relative Score Calculation
# ==========================================

def calculate_relative_score(intraday, swing, atr_weight, momentum, bos=False):

    score = (
        intraday * 0.4 +
        swing * 0.3 +
        atr_weight * 0.2 +
        momentum * 0.1
    )

    # BOS Boost (Break of Structure confirmation)
    if bos:
        score += 5

    return round(score, 2)


# ==========================================
# 🔹 Hybrid Selection Logic
# ==========================================

def select_best_index(index_data):

    if not index_data:
        return None, "No Data"

    # Sort by relative score
    sorted_indices = sorted(
        index_data.items(),
        key=lambda item: item[1]["relative_score"],
        reverse=True
    )

    best_name, best_data = sorted_indices[0]

    # ------------------------------------------
    # If more than one index present
    # ------------------------------------------

    if len(sorted_indices) > 1:

        second_name, second_data = sorted_indices[1]

        diff = best_data["relative_score"] - second_data["relative_score"]

        # ======================================
        # 🔁 ROTATION MODE
        # ======================================

        if diff >= 2.5:
            return best_name, "Rotation Strength Confirmed"

        # ======================================
        # 🔥 DIRECTIONAL MODE
        # ======================================

        both_intraday_strong = (
            best_data["intraday"] >= 80 and
            second_data["intraday"] >= 80
        )

        momentum_aligned = (
            (best_data["momentum"] < 0 and second_data["momentum"] < 0) or
            (best_data["momentum"] > 0 and second_data["momentum"] > 0)
        )

        if both_intraday_strong and momentum_aligned:
            return best_name, "Directional Trend Alignment"

        return None, "Rotation strength too weak"

    # ------------------------------------------
    # Single index fallback
    # ------------------------------------------

    if best_data["intraday"] < 75:
        return None, "Intraday strength insufficient"

    return best_name, "Single Index Mode"