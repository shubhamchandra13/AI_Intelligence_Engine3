# ============================================================
# ROTATION ENGINE – SMART TIE BREAK VERSION
# ============================================================

def select_best_index(index_data):

    if not index_data:
        return None, "No Data"

    sorted_indices = sorted(
        index_data.items(),
        key=lambda item: item[1].get("relative_score", 0.0),
        reverse=True
    )

    best_name, best_data = sorted_indices[0]

    # Single index case
    if len(sorted_indices) == 1:
        if best_data["relative_score"] >= 55:
            return best_name, "Single Index Strong"
        else:
            return None, "Weak Single Index"

    second_name, second_data = sorted_indices[1]

    score_gap = best_data["relative_score"] - second_data["relative_score"]

    # 🔥 Tie Break Logic
    if score_gap == 0:
        return best_name, "Tie Break – First Ranked Selected"

    # 🔥 Balanced Logic for Trending Markets
    if score_gap < 1.0: 
        # 🚀 Directional Mode: If both are strongly aligned (score > 45), trade the best one
        if best_data.get("relative_score", 0) > 45:
            return best_name, f"Directional Mode - Both Strong (Gap {round(score_gap,2)})"
        return None, "Gap too small in weak market"

    # 🔥 Absolute Strength Selection (Works for Bullish & Bearish)
    if abs(best_data["relative_score"]) < 0.1: 
        return None, "Market completely flat"

    return best_name, f"Strongest Index (Score {round(best_data['relative_score'],2)})"