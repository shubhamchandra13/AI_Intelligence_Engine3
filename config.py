# ==========================================
# GLOBAL SETTINGS – AI QUANT ENGINE (PRO LIVE)
# ==========================================

SETTINGS = {

    # ================= CAPITAL =================
    "INITIAL_CAPITAL": 100000,

    # ================= MODE CONTROL =================
    "MODE": "INSTITUTIONAL_PAPER",

    # ================= TEST CONTROL =================
    "FORCE_MARKET_OPEN": False,   # Continuous scanning enabled for simulation

    # ================= SYMBOLS =================
    "SYMBOLS": ["BANKNIFTY", "NIFTY"],

    # ================= LOOP ARCHITECTURE =================
    "FAST_LOOP_INTERVAL": 1,
    "STRUCTURE_SCAN_INTERVAL": 2, # Was 5 - Faster setup detection
    "CANDLE_LIMIT": 2000,
    "MARKET_DATA_STALE_MINUTES": 10, # Was 3 - Be more relaxed during incubation

    # ================= RISK CONTROL =================
    "MIN_CONFIDENCE": 15, # Aggressive Floor for high-freq learning
    "DAILY_MAX_DRAWDOWN_PCT": 40, # High tolerance for aggressive testing
    "AUTO_TUNE_MIN_CONFIDENCE": True, 
    "AUTO_TUNE_LOOKBACK_TRADES": 20, # Very fast learning cycle
    "AUTO_TUNE_MIN_SAMPLES": 5, 
    "AUTO_TUNE_INTERVAL_SECONDS": 30, 
    "AUTO_TUNE_CONFIDENCE_FLOOR": 10, # Allow very aggressive entries
    "AUTO_TUNE_CONFIDENCE_CEILING": 25, 
    "AUTO_TUNE_CONFIDENCE_STEP": 1,
    "AUTO_TUNE_TARGET_WIN_RATE": 45, # Focus on R:R, not just win rate
    "STRICT_ENTRY_MODE": False,
    "BLOCK_IF_MODEL_UNAVAILABLE": False,
    "MIN_STAT_WIN_PROBABILITY": 35,
    "MIN_ML_WIN_PROBABILITY": 35, 
    "MIN_META_QUALITY_PROBABILITY": 35,
    "REQUIRE_META_TAKE_RECOMMENDATION": False,
    "MAX_TRADES_PER_DAY": 50, # Maximize learning opportunities
    "LOSS_COOLDOWN_MINUTES": 0, # No fear, immediate re-entry
    "MAX_CONSECUTIVE_LOSSES": 20, # Keep trying until it works
    "PARTIAL_PROFIT_TRIGGER_PCT": 20, # Aim for bigger initial moves
    "PARTIAL_BOOK_FRACTION": 0.3, # Book less, let winners run
    "PROFIT_LOCK_ACTIVATION_PCT": 15, # Give trade room to breathe
    "MIN_PROFIT_LOCK_PCT": 5,
    "TRAILING_BUFFER_PCT": 10, # Wider trail to avoid noise exits
    "SAME_STRIKE_COOLDOWN_MINUTES": 0,
    "INDEX_EXIT_RULES": {
        "NIFTY": {
            "PARTIAL_PROFIT_TRIGGER_PCT": 10,
            "PARTIAL_BOOK_FRACTION": 0.5,
            "PROFIT_LOCK_ACTIVATION_PCT": 8,
            "MIN_PROFIT_LOCK_PCT": 4,
            "TRAILING_BUFFER_PCT": 5,
            "SAME_STRIKE_COOLDOWN_MINUTES": 0
        },
        "BANKNIFTY": {
            "PARTIAL_PROFIT_TRIGGER_PCT": 14,
            "PARTIAL_BOOK_FRACTION": 0.6,
            "PROFIT_LOCK_ACTIVATION_PCT": 12,
            "MIN_PROFIT_LOCK_PCT": 6,
            "TRAILING_BUFFER_PCT": 7,
            "SAME_STRIKE_COOLDOWN_MINUTES": 0
        },
        "FINNIFTY": {
            "PARTIAL_PROFIT_TRIGGER_PCT": 12,
            "PARTIAL_BOOK_FRACTION": 0.5,
            "PROFIT_LOCK_ACTIVATION_PCT": 10,
            "MIN_PROFIT_LOCK_PCT": 5,
            "TRAILING_BUFFER_PCT": 6,
            "SAME_STRIKE_COOLDOWN_MINUTES": 0
        },
        "MIDCAPNIFTY": {
            "PARTIAL_PROFIT_TRIGGER_PCT": 12,
            "PARTIAL_BOOK_FRACTION": 0.5,
            "PROFIT_LOCK_ACTIVATION_PCT": 10,
            "MIN_PROFIT_LOCK_PCT": 5,
            "TRAILING_BUFFER_PCT": 6,
            "SAME_STRIKE_COOLDOWN_MINUTES": 0
        }
    },
    "EXPIRY_DAY_PROFILE_ENABLED": True,
    "EXPIRY_DAY_INDEX_EXIT_RULES": {
        "NIFTY": {
            "PARTIAL_PROFIT_TRIGGER_PCT": 8,
            "PARTIAL_BOOK_FRACTION": 0.65,
            "PROFIT_LOCK_ACTIVATION_PCT": 6,
            "MIN_PROFIT_LOCK_PCT": 3.5,
            "TRAILING_BUFFER_PCT": 4,
            "SAME_STRIKE_COOLDOWN_MINUTES": 0
        },
        "BANKNIFTY": {
            "PARTIAL_PROFIT_TRIGGER_PCT": 10,
            "PARTIAL_BOOK_FRACTION": 0.7,
            "PROFIT_LOCK_ACTIVATION_PCT": 8,
            "MIN_PROFIT_LOCK_PCT": 4,
            "TRAILING_BUFFER_PCT": 5,
            "SAME_STRIKE_COOLDOWN_MINUTES": 0
        }
    },
    "AI_DECISION_ENGINE": True,
    "MIN_ENTRY_QUALITY_SCORE": 45, # Was 65
    "MAX_UNCERTAINTY_SCORE_TO_TRADE": 80, # Was 60
    "MIN_ML_SAMPLES_FOR_CONFIDENCE": 5, # Was 10
    "HARD_BLOCK_ON_EXTREME_UNCERTAINTY": False, # Was True
    "RISK_REDUCTION_ON_LOW_QUALITY": 0.8,
    "RISK_REDUCTION_ON_HIGH_UNCERTAINTY": 0.7,
    "ML_RETRAIN_SCHEDULE": "DAILY",
    "ML_WEEKLY_RETRAIN_WEEKDAY": 5,
    "ML_WEEKLY_RETRAIN_HOUR_IST": 8,
    "ML_ACCEPTANCE_MIN_EDGE": 0.001,
    "EXECUTION_MAX_SPREAD_PCT": 3.0, # Was 1.5 - More relaxed
    "STRICT_SENTIMENT_ALIGNMENT": False,  # Was True - Don't block during training
    "ADAPTIVE_LOT_SIZING": True,
    "EXECUTION_MIN_LIQUIDITY_SCORE": 20, # Was 35
    "EXECUTION_MAX_SLIPPAGE_PCT": 1.5, # Was 0.8
    "PORTFOLIO_DEFAULT_TARGET_CAPITAL_PCT": 0.22,
    "PORTFOLIO_MAX_SYMBOL_EXPOSURE_PCT": 0.40,
    "PORTFOLIO_MIN_TARGET_CAPITAL_PCT": 0.08,
    "INDICATOR_MTF_RULES": ["1T", "3T", "5T", "15T", "30T"],
    "INDICATOR_MTF_WEIGHTS": {
        "1T": 0.15,
        "3T": 0.20,
        "5T": 0.25,
        "15T": 0.25,
        "30T": 0.15
    },

    # ================= BACKTEST =================
    "BACKTEST_MODE": False,

    # ================= EXPIRY =================
    "EXPIRY_DATE": None,

    # ================= REPLAY SETTINGS =================
    "REPLAY_LOOKBACK_MONTHS": 3,
    "REPLAY_SYMBOLS": ["BANKNIFTY", "NIFTY"],
    "REPLAY_INTERVAL": "1minute",
    "REPLAY_MAX_DAYS_PER_BATCH": 30,
    "REPLAY_START_DATE": None,
    "REPLAY_END_DATE": None,

    # ================= DERIVATIVES KEYS =================
    "INSTRUMENT_KEYS": {
        "BANKNIFTY": "NSE_INDEX|Nifty Bank",
        "NIFTY": "NSE_INDEX|Nifty 50",
        "FINNIFTY": "NSE_INDEX|Nifty Fin Service",
        "MIDCAPNIFTY": "NSE_INDEX|NIFTY MIDCAP 100"
    }
}
