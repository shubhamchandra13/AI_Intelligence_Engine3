# ============================================
# CONFIDENCE ENGINE – AGGRESSIVE ADAPTATION V4
# Optimized with HMM, PCA, LSTM, and ANOMALY AI Layers
# ============================================

def calculate_confidence(structure, mtf_bias, liquidity, fvg, volatility, relative_score, regime, sentiment_score=0.0, vsa_data=None, ofi_data=None, hmm_data=None, pca_data=None, lstm_data=None, anomaly_data=None):
    details = {}
    tech_bias = structure.get("bias", "Neutral").upper()
    
    # ----------------------------------------
    # 1️⃣ STRUCTURE & TREND (Weight: 25%)
    # ----------------------------------------
    structure_score = 0
    if structure.get("bias") in ["Bullish", "Bearish"]:
        structure_score += 25
    if structure.get("bos", False):
        structure_score += 15
    details["structure"] = structure_score

    # ----------------------------------------
    # 2️⃣ LIQUIDITY & FVG (Weight: 15%)
    # ----------------------------------------
    liquidity_score = 5 
    if "Sweep" in liquidity.get("status", ""):
        liquidity_score += 10
    
    fvg_score = 5 
    if fvg.get("status") in ["BULLISH", "BEARISH"] and fvg.get("status") == tech_bias:
        fvg_score = 15
    details["liquidity"] = round(liquidity_score, 2)
    details["fvg"] = fvg_score

    # ----------------------------------------
    # 3️⃣ MTF & MOMENTUM (Weight: 15%)
    # ----------------------------------------
    mtf_val = mtf_bias.get("label", "NEUTRAL") if isinstance(mtf_bias, dict) else mtf_bias
    mtf_score = 0
    if tech_bias in str(mtf_val).upper():
        mtf_score = 25 
    else:
        mtf_score = 10
    details["mtf"] = mtf_score

    # ----------------------------------------
    # 4️⃣ 🧠 LOCAL AI: HMM ALIGNMENT (Weight: 15%)
    # ----------------------------------------
    hmm_score = 0
    if hmm_data and hmm_data.get("label") != "INITIALIZING":
        hmm_label = hmm_data.get("label", "")
        if (tech_bias == "BULLISH" and hmm_label == "HMM_BULLISH") or \
           (tech_bias == "BEARISH" and hmm_label == "HMM_BEARISH"):
            hmm_score = 25
        elif hmm_label == "HMM_SIDEWAYS":
            hmm_score = 10
        else:
            hmm_score = -10 
    details["hmm_alignment"] = hmm_score

    # ----------------------------------------
    # 5️⃣ 🧪 PCA DENOISING: SIGNAL STRENGTH (Weight: 15%)
    # ----------------------------------------
    pca_score = 0
    if pca_data and pca_data.get("status") != "ERROR":
        pca_signal = pca_data.get("signal", 50)
        if tech_bias == "BULLISH" and pca_signal > 60:
            pca_score = 25
        elif tech_bias == "BEARISH" and pca_signal < 40:
            pca_score = 25
        elif 40 <= pca_signal <= 60:
            pca_score = 10
    details["pca_denoising"] = pca_score

    # ----------------------------------------
    # 6️⃣ 🔮 LSTM LOOK-AHEAD: FUTURE TREND (Weight: 15%)
    # ----------------------------------------
    lstm_score = 0
    if lstm_data and lstm_data.get("status") == "READY":
        lstm_dir = lstm_data.get("direction", "")
        if (tech_bias == "BULLISH" and lstm_dir == "UPWARD") or \
           (tech_bias == "BEARISH" and lstm_dir == "DOWNWARD"):
            lstm_score = 25
        elif lstm_dir == "NEUTRAL":
            lstm_score = 10
        else:
            lstm_score = -15 
    details["lstm_lookahead"] = lstm_score

    # ----------------------------------------
    # 7️⃣ 🚨 ANOMALY DETECTION: SAFETY FILTER
    # ----------------------------------------
    anomaly_penalty = 1.0
    if anomaly_data and anomaly_data.get("is_anomaly"):
        anomaly_penalty = 0.5 
        details["anomaly_alert"] = "YES (RISK HIGH)"
    else:
        details["anomaly_alert"] = "NO (SAFE)"

    # ==========================================================
    # 🔥 FINAL WEIGHTED CALCULATION
    # ==========================================================
    weighted_score = (
        structure_score * 0.25 + 
        mtf_score * 0.15 +       
        hmm_score * 0.15 +       
        pca_score * 0.15 +       
        lstm_score * 0.15 +       
        liquidity_score * 0.075 + 
        fvg_score * 0.075
    )

    # Regime Multiplier
    regime_name = regime.get("regime", "")
    regime_multiplier = 1.3 if "TREND" in regime_name else 1.1

    # Normalization to 0-100
    base_confidence = (weighted_score / 25) * 100 
    final_confidence = (base_confidence * regime_multiplier) * anomaly_penalty
    
    # Sentiment Adjustment
    if sentiment_score < -0.2 and tech_bias == "BEARISH": final_confidence *= 1.1
    if sentiment_score > 0.2 and tech_bias == "BULLISH": final_confidence *= 1.1

    final_confidence = max(0.0, min(100.0, final_confidence))

    if final_confidence >= 75: grade = "PRO (A)"
    elif final_confidence >= 55: grade = "SPECULATIVE (B)"
    elif final_confidence >= 35: grade = "RETAIL (C)"
    else: grade = "AVOID"

    return {
        "confidence": round(final_confidence, 2),
        "grade": grade,
        "details": details
    }
