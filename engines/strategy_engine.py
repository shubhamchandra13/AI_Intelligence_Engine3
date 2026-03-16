import pandas as pd
from config import SETTINGS

# Engine Imports
from core.structure_engine import analyze_structure
from core.multi_timeframe import get_multi_timeframe_bias
from core.volatility_engine import detect_volatility_expansion
from core.liquidity_engine import detect_liquidity
from core.fvg_engine import detect_fvg
from core.relative_strength_engine import calculate_relative_score
from core.vsa_engine import VSAEngine
from core.market_intelligence_v2 import MarketIntelligenceV2
from core.hmm_regime_engine import HMMRegimeEngine
from core.denoising_pca_engine import DenoisingPCAEngine
from core.lstm_forecaster_engine import LSTMForecasterEngine
from core.anomaly_detection_engine import AnomalyDetectionEngine
from core.meta_learning_engine import MetaLearningEngine
from core.trap_detection_engine import TrapDetectionEngine

from engines.confidence_engine import calculate_confidence
from engines.adaptive_risk_engine import AdaptiveRiskEngine
from engines.regime_detection_engine import RegimeDetectionEngine
from engines.regime_clustering_engine import RegimeClusteringEngine
from engines.trade_intelligence_engine import TradeIntelligenceEngine
from engines.iv_volatility_engine import IVVolatilityEngine
from engines.target_multiplier_engine import TargetMultiplierEngine
from engines.auto_threshold_engine import AutoThresholdEngine
from indicators import evaluate_mtf_indicator_stack

class StrategyEngine:
    """
    Central brain for making trading decisions.
    Used by both Live Paper Trading and Historical Replay.
    """
    def __init__(self):
        # Initialize sub-engines
        self.regime_engine = RegimeDetectionEngine()
        self.vsa_engine = VSAEngine()
        self.adaptive_risk_engine = AdaptiveRiskEngine()
        self.trade_intel_engine = TradeIntelligenceEngine()
        self.iv_engine = IVVolatilityEngine()
        self.target_engine = TargetMultiplierEngine()
        self.meta_engine = MetaLearningEngine()
        self.trap_engine = TrapDetectionEngine()
        self.market_intel = MarketIntelligenceV2()
        self.regime_clustering_engine = RegimeClusteringEngine()
        
        # Advanced AI Engines (Stateful)
        self.hmm_engine = HMMRegimeEngine(n_states=3)
        self.pca_engine = DenoisingPCAEngine(n_components=3)
        self.anomaly_engine = AnomalyDetectionEngine()
        self.lstm_engines = {sym: LSTMForecasterEngine(window_size=60, forecast_steps=10) for sym in SETTINGS["SYMBOLS"]}
        
        # Threshold Engine
        self.threshold_engine = AutoThresholdEngine(
            db_path="database/trades.db",
            lookback_trades=SETTINGS.get("AUTO_TUNE_LOOKBACK_TRADES", 50),
            min_samples=SETTINGS.get("AUTO_TUNE_MIN_SAMPLES", 10),
            tune_interval_seconds=SETTINGS.get("AUTO_TUNE_INTERVAL_SECONDS", 60),
            min_confidence_floor=SETTINGS.get("AUTO_TUNE_CONFIDENCE_FLOOR", 18),
            max_confidence_ceiling=SETTINGS.get("AUTO_TUNE_CONFIDENCE_CEILING", 85),
            confidence_step=SETTINGS.get("AUTO_TUNE_CONFIDENCE_STEP", 2),
            target_win_rate=SETTINGS.get("AUTO_TUNE_TARGET_WIN_RATE", 48.0)
        )
        self.dynamic_min_confidence = SETTINGS.get("MIN_CONFIDENCE", 20)

    def update_thresholds(self):
        """
        Updates dynamic confidence thresholds based on recent performance.
        """
        tuning_res = self.threshold_engine.maybe_tune(self.dynamic_min_confidence)
        if SETTINGS.get("AUTO_TUNE_MIN_CONFIDENCE", True):
            if tuning_res.get("status") == "tuned":
                self.dynamic_min_confidence = tuning_res["min_confidence"]
                return True, tuning_res
        return False, None

    def analyze_symbol(self, symbol, df, spot_price, market_context=None):
        """
        Runs the full analysis pipeline on a single symbol.
        """
        if df is None or df.empty:
            return None

        # 1. Basic Technical Analysis
        struc = analyze_structure(df)
        reg = self.regime_engine.detect_regime(df)
        mtf = get_multi_timeframe_bias(df)
        vs = self.vsa_engine.analyze(df)
        liq = detect_liquidity(df)
        fv = detect_fvg(df, struc["bias"].upper())
        vol_exp = detect_volatility_expansion(df)
        stk = evaluate_mtf_indicator_stack(df, SETTINGS.get("INDICATOR_MTF_RULES"), SETTINGS.get("INDICATOR_MTF_WEIGHTS"))

        # 2. Advanced AI Analysis
        hmm_data = self.hmm_engine.detect_regime(df)
        pca_data = self.pca_engine.get_clean_signal(df)
        anomaly_data = self.anomaly_engine.check_anomaly(df)
        
        # LSTM Forecast
        lstm_data = {"status": "INITIALIZING", "direction": "NEUTRAL", "forecast_diff_pct": 0.0}
        target_lstm = self.lstm_engines.get(symbol)
        if target_lstm:
            try:
                # Note: Training should ideally happen in a background thread or less frequently
                # For now, we follow the pattern but maybe skip training here to keep it fast
                # target_lstm.train_incremental(df) # Moved out or controlled externally
                res = target_lstm.predict_future(df)
                if res: lstm_data = res
            except Exception:
                pass

        # 3. Market Context & Relative Strength
        intraday_ret = 0.0
        swing_ret = 0.0
        if len(df) > 0:
            intraday_ret = ((spot_price / df["close"].iloc[0]) - 1) * 1000
            # Approx 5 days * 375 mins
            five_day_idx = -min(len(df), 375 * 5)
            swing_ret = ((spot_price / df["close"].iloc[five_day_idx]) - 1) * 1000
        
        rel_score = calculate_relative_score(
            intraday=intraday_ret, 
            swing=swing_ret, 
            atr_weight=0.5, 
            momentum=stk.get("score", 50), 
            bos=struc.get("bos", False)
        )

        # 4. Intelligence Layers
        # Need other_df for market_intel.analyze_market_mode
        # market_context should provide this if available
        intel_data = {"mode": "NORMAL"}
        if market_context and "other_df" in market_context:
             intel_data = self.market_intel.analyze_market_mode(df, market_context["other_df"])

        self.meta_engine.refresh_knowledge()
        meta_mult, meta_reason = self.meta_engine.judge_setup(reg["regime"], 60)
        trap_data = self.trap_engine.detect_trap(df)
        reg_v2 = self.regime_clustering_engine.detect_regime_v2(df)
        
        # 5. Volatility & Risk
        iv_data = market_context.get("iv_data", {"current_iv": 0.0, "iv_regime": "NORMAL_IV"}) if market_context else {"current_iv": 0.0, "iv_regime": "NORMAL_IV"}
        ofi_data = market_context.get("ofi_data", {}) if market_context else {}
        current_sentiment = market_context.get("sentiment", 0.0) if market_context else 0.0
        ml_prediction = market_context.get("ml_prediction", {"win_probability": 50.0}) if market_context else {"win_probability": 50.0}

        # 6. Confidence Calculation
        conf = calculate_confidence(
            structure=struc, 
            mtf_bias=mtf, 
            liquidity=liq, 
            fvg=fv, 
            volatility=vol_exp, 
            relative_score=rel_score, 
            regime=reg, 
            sentiment_score=current_sentiment*0.5, 
            vsa_data=vs, 
            ofi_data=ofi_data, 
            hmm_data=hmm_data, 
            pca_data=pca_data, 
            lstm_data=lstm_data, 
            anomaly_data=anomaly_data
        )

        # Meta-Adjustment
        orig_c = conf["confidence"]
        conf["confidence"] = min(100.0, orig_c * meta_mult)
        if trap_data["status"] == "TRAP_DETECTED":
            conf["confidence"] = max(conf["confidence"], 85.0)
        
        if intel_data["mode"] == "OPTION_SELLER_DOMINATED":
            conf["confidence"] *= 0.7

        # 7. Risk Calculation
        stats = self.trade_intel_engine.get_basic_stats()
        d_risk = self.adaptive_risk_engine.calculate_dynamic_risk(
            confidence=conf["confidence"], 
            regime=reg, 
            iv_data=iv_data, 
            intelligence_stats=stats
        )

        return {
            "symbol": symbol,
            "spot": spot_price,
            "structure": struc,
            "regime": reg,
            "regime_v2": reg_v2,
            "confidence": conf,
            "liquidity": liq,
            "fvg": fv,
            "vsa": vs,
            "indicator_stack": stk,
            "relative_score": rel_score,
            "ml_prediction": ml_prediction,
            "lstm_data": lstm_data,
            "hmm_data": hmm_data,
            "pca_data": pca_data,
            "anomaly_data": anomaly_data,
            "trap_data": trap_data,
            "intel_data": intel_data,
            "high": df["high"].max(),
            "low": df["low"].min(),
            "iv_data": iv_data,
            "risk": d_risk,
            "ofi_data": ofi_data
        }

    def make_decision(self, analysis_result):
        """
        Determines if a trade should be taken based on analysis result.
        """
        if not analysis_result:
            return {"action": "WAITING", "reason": "No analysis result"}

        conf_val = analysis_result["confidence"]["confidence"]
        action = "READY" if conf_val >= self.dynamic_min_confidence else "WAITING"
        
        return {
            "action": action,
            "symbol": analysis_result["symbol"],
            "confidence": conf_val,
            "threshold": self.dynamic_min_confidence,
            "regime": analysis_result["regime"]["regime"],
            "bias": analysis_result["structure"]["bias"]
        }
