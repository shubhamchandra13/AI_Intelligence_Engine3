# ============================================================
# 🤖 AI ALPHA SYSTEM TERMINAL - FULL INSTITUTIONAL DESK (v10.5)
# FINAL PRODUCTION VERSION - STABLE, EXHAUSTIVE, CLEAN
# ============================================================

import time
import os
import sys
import threading
import queue
import warnings
import logging
import contextlib
import ctypes
import traceback
import copy
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, time as dtime
import pytz
import pandas as pd
import msvcrt

# Try to import psutil for telemetry
try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False

# --- SILENCE LIBRARIES (STABLE) ---
os.environ["TRANSFORMERS_VERBOSITY"] = "error"
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"
os.environ["HF_HUB_DISABLE_PROGRESS_BARS"] = "1"
os.environ["PYTHONWARNINGS"] = "ignore"
os.environ["BITSANDBYTES_NOWELCOME"] = "1"
warnings.filterwarnings("ignore")
import logging
logging.getLogger("transformers").setLevel(logging.ERROR)
logging.getLogger("torch").setLevel(logging.ERROR)

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

# --- CORE & ENGINE IMPORTS ---
from config import SETTINGS
from core.data_fetcher import DataFetcher
from core.structure_engine import analyze_structure
from core.multi_timeframe import get_multi_timeframe_bias
from core.volatility_engine import detect_volatility_expansion
from core.liquidity_engine import detect_liquidity
from core.fvg_engine import detect_fvg
from core.relative_strength_engine import calculate_relative_score
from core.rotation_engine import select_best_index
from core.upstox_client import UpstoxClient
from core.upstox_websocket_engine import UpstoxWebsocketEngine
from core.vsa_engine import VSAEngine
from core.sentiment_engine import SentimentEngine
from core.order_book_analyzer import OrderBookAnalyzer
from core.runtime_control import read_control_state, write_runtime_state, pop_actions
from core.intermarket_analysis import detect_smt_divergence
from core.health_check import HealthCheck
from core.data_guards import DataGuards
from core.knowledge_engine import KnowledgeEngine
from core.inter_asset_engine import InterAssetEngine
from core.volatility_forecaster import VolatilityForecaster
from core.meta_learning_engine import MetaLearningEngine
from core.trap_detection_engine import TrapDetectionEngine
from core.market_intelligence_v2 import MarketIntelligenceV2
from core.hmm_regime_engine import HMMRegimeEngine
from core.denoising_pca_engine import DenoisingPCAEngine
from core.lstm_forecaster_engine import LSTMForecasterEngine
from core.anomaly_detection_engine import AnomalyDetectionEngine

from engines.confidence_engine import calculate_confidence
from engines.strike_selection_engine import StrikeSelectionEngine
from engines.adaptive_risk_engine import AdaptiveRiskEngine
from engines.regime_detection_engine import RegimeDetectionEngine
from engines.regime_clustering_engine import RegimeClusteringEngine
from engines.rl_position_sizing_engine import RLPositionSizingEngine
from engines.institutional_paper_execution_engine import InstitutionalPaperExecutionEngine
from engines.performance_engine import PerformanceEngine
from engines.execution_quality_engine import ExecutionQualityEngine
from engines.trade_intelligence_engine import TradeIntelligenceEngine
from engines.ml_evolution_engine import MLEvolutionEngine
from engines.safe_notifier import SafeNotifier
from engines.iv_volatility_engine import IVVolatilityEngine
from engines.greeks_engine import GreeksEngine
from engines.theta_engine import ThetaEngine
from engines.target_multiplier_engine import TargetMultiplierEngine
from engines.auto_threshold_engine import AutoThresholdEngine
from engines.genetic_optimizer import GeneticOptimizer
from indicators import evaluate_mtf_indicator_stack

# Global objects
data_fetcher = DataFetcher(); strike_engine = StrikeSelectionEngine()
adaptive_risk_engine = AdaptiveRiskEngine(); regime_engine = RegimeDetectionEngine()
vsa_engine = VSAEngine(); upstox_client = UpstoxClient()
rl_position_engine = RLPositionSizingEngine()
execution_engine = InstitutionalPaperExecutionEngine(initial_capital=SETTINGS["INITIAL_CAPITAL"], rl_engine=rl_position_engine)
meta_engine = MetaLearningEngine()
trap_engine = TrapDetectionEngine()
market_intel = MarketIntelligenceV2()

trade_intelligence_engine = TradeIntelligenceEngine()
ml_engine = None # Async load
genetic_optimizer = GeneticOptimizer() # 🔥 GENESIS AI
order_book_engine = OrderBookAnalyzer()
safe_notifier = SafeNotifier()
iv_engine = IVVolatilityEngine()
greeks_engine = GreeksEngine()
theta_engine = ThetaEngine()
target_engine = TargetMultiplierEngine()
vol_forecaster = VolatilityForecaster()
regime_clustering_engine = RegimeClusteringEngine()
execution_quality_engine = ExecutionQualityEngine()

# 🔥 PHASE 1: AUTO-THRESHOLD ENGINE (SELF-TUNING BRAIN)
threshold_engine = AutoThresholdEngine(
    db_path="database/trades.db",
    lookback_trades=SETTINGS.get("AUTO_TUNE_LOOKBACK_TRADES", 50),
    min_samples=SETTINGS.get("AUTO_TUNE_MIN_SAMPLES", 10),
    tune_interval_seconds=SETTINGS.get("AUTO_TUNE_INTERVAL_SECONDS", 60),
    min_confidence_floor=SETTINGS.get("AUTO_TUNE_CONFIDENCE_FLOOR", 18),
    max_confidence_ceiling=SETTINGS.get("AUTO_TUNE_CONFIDENCE_CEILING", 85),
    confidence_step=SETTINGS.get("AUTO_TUNE_CONFIDENCE_STEP", 2),
    target_win_rate=SETTINGS.get("AUTO_TUNE_TARGET_WIN_RATE", 48.0)
)
# Load initial threshold
_initial_ctrl = read_control_state()
dynamic_min_confidence = _initial_ctrl.get("overrides", {}).get("DYNAMIC_MIN_CONFIDENCE", SETTINGS.get("MIN_CONFIDENCE", 70))

# --- REAL-TIME WEBSOCKET INITIALIZATION ---
all_instr_keys = list(SETTINGS["INSTRUMENT_KEYS"].values())
ws_engine = UpstoxWebsocketEngine(instrument_keys=all_instr_keys)
ws_engine.start()

# --- UI STATE & TIMEZONE ---
IST = pytz.timezone("Asia/Kolkata")
ui_events = queue.Queue()
ai_events = queue.Queue()
recent_logs = []
recent_ai_logs = []
boot_time = datetime.now(IST)

# Baseline data
initial_map = {
    sym: {
        "spot": 0.0, "high": 0.0, "low": 0.0, "structure": {"bias": "Neutral"},
        "regime": {"regime": "SCANNING"}, "confidence": {"confidence": 0.0},
        "ml_prediction": {"win_probability": 50.0}, "fvg": {"status": "NONE"},
        "vsa": {"vsa_signal": "Normal"}, "liquidity": {"status": "N/A"},
        "iv_data": {"current_iv": 0.0, "iv_regime": "NORMAL_IV"},
        "oi_data": {"bias": "NEUTRAL"},
        "relative_score": 0.0
    } for sym in SETTINGS["SYMBOLS"]
}

shared_state = {
    "analysis_map": initial_map, "best_index": None, "news_sentiment": 0.0,
    "news_items": [],
    "db_stats": {}, "system_status": "RUNNING", "neural_ready": False,
    "ml_ready": False,
    "scan_count": 0, "ob_data": {}, "smt_status": {"status": "SYNCED", "reason": "Synced"},
    "expiry": "N/A", "current_iv": 0.0, "iv_regime": "NORMAL_IV", "theta_risk": "SAFE",
    "entry_paused": False, "rotation_reason": "Scanning...",
    "strategy_status": "WAITING FOR SETUP...",
    "why_no_trade": [],
    "macro_status": {"macro_score": 0.0, "macro_bias": "NEUTRAL", "details": {}},
    "last_updated": {"neural": None, "structural": None, "ml": None, "db": None, "genesis": None},
    "decision_output": {
        "action": "NO-TRADE",
        "headline": "System warming up",
        "summary": "Initial market scan pending.",
        "reasons": ["Live analysis not ready yet."],
        "symbol": None,
        "bias": "NEUTRAL",
        "regime": "SCANNING",
        "confidence": 0.0,
        "grade": "N/A",
        "risk_status": "PENDING",
        "entry_allowed": False,
        "market_open": False,
        "strategy_status": "WAITING FOR SETUP...",
        "spot": 0.0,
        "targets": {"entry": None, "stop": None, "target": None},
        "option_plan": {},
        "diagnostics": {},
        "rationale": [],
    }
}
state_lock = threading.Lock()

# ======================= UI UTILITIES =======================

ANSI = {
    "reset": "\033[0m", "bold": "\033[1m", "red": "\033[31m", "green": "\033[32m", 
    "yellow": "\033[33m", "blue": "\033[34m", "magenta": "\033[35m", "cyan": "\033[36m", "white": "\033[37m",
    "home": "\033[H", "clear": "\033[2J", "hide_cursor": "\033[?25l", "show_cursor": "\033[?25h"
}

def _color(text, fg=None, bold=False):
    p = ANSI["bold"] if bold else ""
    if fg and fg in ANSI: p += ANSI[fg]
    return f"{p}{text}{ANSI['reset']}"

def ui_log(msg):
    formatted_msg = f"[{datetime.now().strftime('%H:%M:%S')}] {msg}"
    ui_events.put(formatted_msg)

def ai_log(msg):
    formatted_msg = f"[{datetime.now().strftime('%H:%M:%S')}] {msg}"
    ai_events.put(formatted_msg)

def _to_ist_timestamp(series):
    ts = pd.to_datetime(series)
    if ts.dt.tz is None: return ts.dt.tz_localize(IST)
    return ts.dt.tz_convert(IST)

def market_status_info():
    st = read_control_state()
    if st.get("overrides", {}).get("FORCE_MARKET_OPEN"): return "🟢 LIVE (FORCE)", "green", True
    now_ist = datetime.now(IST)
    if now_ist.weekday() >= 5: return "🔴 CLOSED (WEEKEND)", "red", False
    n = now_ist.time()
    if dtime(9, 15) <= n <= dtime(15, 30): return "🟢 LIVE MARKET", "green", True
    elif dtime(9, 0) <= n < dtime(9, 15): return "🟡 PRE-MARKET (DISCOVERY)", "yellow", False
    else: return "🔴 CLOSED (AI-INCUBATION ACTIVE)", "red", False

def market_open():
    _, _, is_open = market_status_info()
    return is_open

def _safe_round(value, digits=2, default=None):
    try: return round(float(value), digits)
    except: return default

# =================== THREADS (BACKGROUND) ===================

def thread_sentiment_scan():
    try:
        with silence_stdout(): engine = SentimentEngine()
        with state_lock: shared_state["neural_ready"] = True
        ui_log("Neural Core Active.")
        while True:
            try:
                s = engine.analyze_sentiment()
                news_items = engine.fetch_headlines_with_time(limit=15)
                with state_lock: 
                    shared_state["news_sentiment"] = s
                    shared_state["news_items"] = news_items
                    shared_state["last_updated"]["neural"] = datetime.now(IST).isoformat()
            except Exception as e: ui_log(f"Neural Scan Error: {e}")
            time.sleep(120)
    except Exception as e: ui_log(f"Neural Error: {e}")

from core.mode_manager import ModeManager
from core.data_provider import DataProvider
from engines.strategy_engine import StrategyEngine

# Initialize core manager
mode_manager = ModeManager()

def thread_structure_scan():
    global ml_engine, dynamic_min_confidence
    strategy_engine = StrategyEngine()
    
    try:
        ml_engine = MLEvolutionEngine()
        with state_lock: shared_state["ml_ready"] = True
        ui_log("AI Brain: ML Core Ready.")
    except Exception as e: ui_log(f"ML Load Error: {e}")

    while True:
        try:
            mode_manager.update_mode()
            if mode_manager.get_mode() == "IDLE":
                time.sleep(5)
                continue

            tuned, tuning_res = strategy_engine.update_thresholds()
            if tuned:
                old_c = dynamic_min_confidence
                dynamic_min_confidence = tuning_res["min_confidence"]
                ai_log(f"🧠 SELF-EVOLUTION: Confidence tuned {old_c} -> {dynamic_min_confidence}")
            else:
                dynamic_min_confidence = SETTINGS.get("MIN_CONFIDENCE", 20)
                if shared_state["scan_count"] % 15 == 0:
                    ai_log(f"🛡️ SAFETY OVERRIDE: Threshold Locked @ {dynamic_min_confidence}%")

            with state_lock: loc = shared_state["analysis_map"].copy()
            dfs = {}
            ctrl = read_control_state()
            entry_paused = ctrl.get("overrides", {}).get("PAUSE_ENTRIES", False)
            with state_lock: current_sentiment = shared_state["news_sentiment"]
            detected_expiry = SETTINGS.get("EXPIRY_DATE")

            # First pass to gather DataFrames
            for sym in SETTINGS["SYMBOLS"]:
                df_raw = data_fetcher.get_candles(sym, interval="1minute", limit=SETTINGS.get("CANDLE_LIMIT", 2000))
                if df_raw is not None:
                    df = pd.DataFrame(df_raw)
                    df["timestamp"] = _to_ist_timestamp(df["timestamp"])
                    df.set_index("timestamp", inplace=True)
                    dfs[sym] = df

            for sym in SETTINGS["SYMBOLS"]:
                instr_key = SETTINGS["INSTRUMENT_KEYS"].get(sym)
                ws_ltp = ws_engine.get_ltp(instr_key)
                s = ws_ltp if (ws_ltp and ws_ltp > 0) else data_fetcher.get_spot(sym)
                
                if s and s > 0:
                    with state_lock:
                        if sym in shared_state["analysis_map"]: shared_state["analysis_map"][sym]["spot"] = s

                is_valid, msg = DataGuards.validate_spot(s, sym)
                if not is_valid:
                    ui_log(f"⚠️ Data Guard: {msg}")
                    continue

                df = dfs.get(sym)
                if df is None: continue

                # Get Option Chain & IV Data first for the context
                target_expiry = SETTINGS.get("EXPIRY_DATE")
                if not target_expiry:
                    all_expiries = upstox_client.get_all_expiries(instr_key)
                    if all_expiries:
                        target_expiry = all_expiries[-1] if sym == "BANKNIFTY" and len(all_expiries) < 4 else all_expiries[0]

                strike_step = 100 if sym == "BANKNIFTY" else 50
                chain = upstox_client.fetch_option_chain(instr_key, target_expiry)
                detected_expiry = target_expiry if target_expiry else upstox_client.last_selected_expiry

                iv_data = {"current_iv": 0.0, "iv_regime": "NORMAL_IV", "tradable": True}
                if chain:
                    atm_strike = round(s / strike_step) * strike_step
                    for _sd in chain:
                        if abs(_sd["strike_price"] - atm_strike) < 10:
                            call_data = _sd.get("call_options")
                            if call_data:
                                iv_val = call_data.get("market_data", {}).get("iv") or 0
                                if iv_val > 0: iv_data = iv_engine.analyze({"current_iv": iv_val})
                                break

                # Prepare Market Context
                depth = upstox_client.fetch_market_depth(instr_key)
                ofi_data = order_book_engine.analyze(depth, current_price=s)
                other_sym = "BANKNIFTY" if sym == "NIFTY" else "NIFTY"
                other_df = dfs.get(other_sym)

                market_context = {
                    "iv_data": iv_data,
                    "ofi_data": ofi_data,
                    "sentiment": current_sentiment,
                    "other_df": other_df
                }

                # --- 🧠 RUN STRATEGY ENGINE ---
                analysis_result = strategy_engine.analyze_symbol(sym, df, s, market_context)
                
                if analysis_result:
                    loc[sym] = analysis_result
                    with state_lock:
                        shared_state["analysis_map"][sym] = loc[sym]

            b, reason = select_best_index(loc)
            
            # --- 🔥 DYNAMIC DECISION LOGIC ---
            best_data = loc.get(b) if b else None
            new_decision = shared_state["decision_output"].copy()
            
            if best_data:
                decision_res = strategy_engine.make_decision(best_data)
                action = decision_res["action"]
                conf_val = decision_res["confidence"]
                
                # Grade logic
                grade = "AVOID"
                if conf_val > 75: grade = "A+"
                elif conf_val > 65: grade = "A"
                elif conf_val > 55: grade = "B"
                elif conf_val >= dynamic_min_confidence: grade = "C"
                
                # Rationale & Blockers
                rationale = [
                    f"Structure bias: {best_data['structure']['bias']}",
                    f"Liquidity: {best_data['liquidity']['status']}",
                    f"Volume bias: {best_data['vsa']['vsa_signal']}"
                ]
                reasons = []
                if conf_val < dynamic_min_confidence:
                    reasons.append(f"Confidence {round(conf_val,1)}% is below threshold {dynamic_min_confidence}%")
                if "Relative score" in reason:
                    reasons.append(f"Rotation engine: {reason}")

                new_decision.update({
                    "action": action,
                    "symbol": b,
                    "headline": "READY TO TRADE" if action == "READY" else "SCANNING FOR SETUP",
                    "summary": f"Confidence: {round(conf_val,1)}% | Regime: {best_data['regime']['regime']}",
                    "spot": best_data["spot"],
                    "confidence": round(conf_val, 1),
                    "bias": best_data["structure"]["bias"],
                    "regime": best_data["regime"]["regime"],
                    "grade": grade,
                    "rationale": rationale,
                    "reasons": reasons,
                    "risk_status": "READY" if action == "READY" else "BLOCKED"
                })

                # 🔥 ACTUAL TRADE EXECUTION (PHASE 2)
                if action == "READY" and not execution_engine.positions and not entry_paused:
                    # Select strike and plan trade
                    direction = "BULLISH" if best_data["structure"]["bias"].upper() == "BULLISH" else "BEARISH"
                    option_type = "CE" if direction == "BULLISH" else "PE"
                    
                    # Get Selected Strike Price
                    sel_res = strike_engine.select_strike(b, best_data["spot"], direction, best_data["regime"], best_data["confidence"]["confidence"], iv_data=best_data["iv_data"])
                    
                    if sel_res and isinstance(sel_res, dict) and chain:
                        sel_strike = float(sel_res.get("strike", 0))
                        
                        # Find Instrument Key from Chain
                        inst_key = None
                        for s_data in chain:
                            try:
                                chain_strike = float(s_data.get("strike_price", 0))
                                if abs(chain_strike - sel_strike) < 5:
                                    opt_data = s_data.get("call_options") if option_type == "CE" else s_data.get("put_options")
                                    if opt_data and opt_data.get("instrument_key"):
                                        inst_key = opt_data.get("instrument_key")
                                        break
                            except: continue
                        
                        # --- LSTM SANITY CHECK ---
                        is_forecast_sane = True
                        if lstm_data["status"] == "READY":
                            # If forecast is more than 5%, it's likely an error/noise
                            if abs(lstm_data["forecast_diff_pct"]) > 5.0:
                                is_forecast_sane = False
                                ai_log(f"⚠️ LSTM IGNORED: Unrealistic forecast ({lstm_data['forecast_diff_pct']}%)")

                        if inst_key and is_forecast_sane:
                            ui_log(f"🚀 EXECUTION TRIGGERED: {b} {sel_strike} {option_type} @ {best_data['spot']}")
                            
                            # Set Target Multiplier
                            t_mult = target_engine.get_adaptive_multiplier(best_data["regime"], confidence=best_data["confidence"]["confidence"], iv_data=best_data["iv_data"])
                            
                            # Prepare Ladder (Single Strike)
                            ladder = [(sel_strike, option_type, inst_key, 1.0)]
                            
                            # Enter Trade
                            execution_engine.enter_trade(
                                index=b,
                                direction=direction,
                                price=best_data["spot"],
                                confidence=best_data["confidence"]["confidence"],
                                df=dfs[b],
                                dynamic_risk=best_data["risk"],
                                target_multiplier=t_mult,
                                ladder_strikes=ladder
                            )
                            
                            new_decision.update({
                                "option_plan": {"strike": sel_strike, "option_type": option_type},
                                "targets": {"entry": best_data["spot"], "stop": "Dynamic", "target": "Dynamic"}
                            })
                        else:
                            ui_log(f"⚠️ STRIKE ERROR: No key for {sel_strike} {option_type}")
                    else:
                        ui_log(f"⚠️ STRIKE ERROR: No strike or chain data")
            
            # Action & Execution logic
            if execution_engine.positions:
                instr_keys = [p.get("instrument_key") for p in execution_engine.positions]
                price_map = data_fetcher.get_ltps(instr_keys)
                if price_map:
                    execution_engine.update_floating_pnl(price_map)
                    closed = execution_engine.check_exit(price_map, df_map=dfs)
                    if closed: ui_log(f"📉 EXIT: {closed['index']} {closed['reason']} at {closed['exit_price']} (PnL: {round(closed['pnl'], 2)})")

            with state_lock: 
                shared_state.update({
                    "analysis_map": loc, 
                    "best_index": b, 
                    "rotation_reason": reason,
                    "scan_count": shared_state["scan_count"]+1, 
                    "expiry": str(detected_expiry),
                    "decision_output": new_decision
                })
                write_runtime_state(shared_state)
            
            time.sleep(SETTINGS.get("STRUCTURE_SCAN_INTERVAL", 2))
        except Exception as e: ui_log(f"Scan Error: {e}"); time.sleep(5)

def thread_db_stats_scan():
    while True:
        try:
            trade_intelligence_engine.refresh()
            stats = trade_intelligence_engine.get_basic_stats()
            with state_lock: shared_state["db_stats"] = stats
        except: pass
        time.sleep(60)

def thread_ml_evolution():
    while True:
        try:
            if ml_engine: ml_engine.maybe_retrain()
        except: pass
        time.sleep(1800)

def thread_genetic_evolution():
    while True:
        try:
            ai_log("🧬 GENESIS AI: Evolving DNA...")
            genetic_optimizer.evolve(logger=ai_log)
        except: pass
        time.sleep(10800)

def thread_macro_scan():
    engine = InterAssetEngine()
    while True:
        try:
            engine.fetch_macro_data()
            res = engine.calculate_macro_bias()
            with state_lock: shared_state["macro_status"] = res
            ai_log(f"🌍 MACRO EYE: {res['macro_bias']}")
        except: pass
        time.sleep(900)

def run():
    hc = HealthCheck(SETTINGS)
    if not hc.run_all(): return
    if os.name == 'nt': 
        os.system('')
        ctypes.windll.kernel32.SetConsoleTitleW("AI Alpha - Institutional Desk v10.5")
    os.system('cls' if os.name == 'nt' else 'clear')
    sys.stdout.write(ANSI["hide_cursor"])
    ex = ThreadPoolExecutor(max_workers=7)
    ex.submit(thread_sentiment_scan); ex.submit(thread_structure_scan)
    ex.submit(thread_db_stats_scan); ex.submit(thread_ml_evolution)
    ex.submit(thread_genetic_evolution); ex.submit(thread_macro_scan)
    time.sleep(2)
    while True:
        try:
            if msvcrt.kbhit():
                key = msvcrt.getch().decode('utf-8').upper()
                if key == 'X':
                    for pos in [p for p in execution_engine.positions if p["index"] == "NIFTY"]:
                        ik = pos.get("instrument_key"); p = ws_engine.get_ltp(ik) or data_fetcher.get_option_ltp(ik)
                        if p: execution_engine.check_exit({ik: p}, df_map={})
                elif key == 'B':
                    for pos in [p for p in execution_engine.positions if p["index"] == "BANKNIFTY"]:
                        ik = pos.get("instrument_key"); p = ws_engine.get_ltp(ik) or data_fetcher.get_option_ltp(ik)
                        if p: execution_engine.check_exit({ik: p}, df_map={})
                elif key == 'A': execution_engine.emergency_exit(reason="Manual Hotkey")
                elif key == 'R':
                    ui_log("♻️ RESTARTING SYSTEM...")
                    time.sleep(1)
                    python = sys.executable
                    os.execv(python, [python] + sys.argv)

            with state_lock: ctx = copy.deepcopy(shared_state)
            amap, best_idx, db_stats, ist_now, decision = ctx["analysis_map"], ctx["best_index"], ctx["db_stats"], datetime.now(IST), ctx["decision_output"]
            while not ui_events.empty():
                recent_logs.append(ui_events.get())
                if len(recent_logs) > 6: recent_logs.pop(0)
            while not ai_events.empty():
                recent_ai_logs.append(ai_events.get())
                if len(recent_ai_logs) > 5: recent_ai_logs.pop(0)

            os.system('cls' if os.name == 'nt' else 'clear')
            f = []
            w = 84
            def out(s, pad=True): 
                line = str(s)
                if pad: line = line.ljust(w)
                f.append(line + "\n")

            out("╔" + "═" * (w-2) + "╗", pad=False)
            out("║" + _color(" 🤖 AI INTELLIGENCE TERMINAL - INSTITUTIONAL DESK ".center(w-2), "cyan", True) + "║", pad=False)
            out("╚" + "═" * (w-2) + "╝", pad=False)
            
            n_stat = _color('READY', 'green') if ctx.get('neural_ready') else _color('LOAD', 'yellow')
            e_stat = _color('PAUSED', 'red', True) if ctx.get('entry_paused') else _color('ACTIVE', 'green')
            m_text, m_color, _ = market_status_info()
            out(f"🕒 {ist_now.strftime('%H:%M:%S')} | Neural: {n_stat} | Entries: {e_stat} | Expiry: {_color(ctx.get('expiry','N/A'), 'yellow')}")
            out(f"Market Status: {_color(m_text, m_color)} | Rotation: {_color(ctx.get('rotation_reason','Scanning'), 'magenta')} | TG: {_color('ON','green')}")
            out("═" * w, pad=False)

            out(_color(f" 📊 MARKET WATCH (Expiry: {ctx.get('expiry','N/A')}) ", "yellow", True).center(w, "═"), pad=False)
            for sym in SETTINGS["SYMBOLS"]:
                d = amap.get(sym, {})
                if d and d.get("spot", 0) > 0:
                    trend_val = d.get("structure", {}).get("bias", "Neutral")
                    trend_sym = _color("▲", "green") if "Bull" in trend_val else _color("▼", "red")
                    out(f" {sym:<12} | Spot: {round(d.get('spot',0),1):<8} | H/L: {round(d.get('high',0),1)}/{round(d.get('low',0),1)} | Trend: {trend_sym}")
                else: out(f" {sym:<12} | [ INITIALIZING MARKET DATA... ]")
            
            smt = ctx.get("smt_status", {})
            out(f" Inter-Market: {_color(smt.get('status','SYNCED'), 'green' if smt.get('status')=='SYNCED' else 'yellow')} | Bias: {smt.get('reason','Indices moving together')}")

            # --- 🔥 MARKET PERSONALITY SECTION ---
            active_idx = best_idx or SETTINGS["SYMBOLS"][0]
            bd = amap.get(active_idx, {})
            intel = bd.get("intel_info", {"mode": "SCANNING", "reason": "Wait...", "action": "HOLD", "color": "white"})
            
            out(_color(" 🧠 MARKET PERSONALITY (Intelligence v2) ", intel.get("color", "blue"), True).center(w, "═"), pad=False)
            out(f" Mode:   {_color(intel.get('mode','SCANNING'), intel.get('color','white'), True):<30} | Sync: {intel.get('sync', 0.0)}")
            out(f" Reason: {intel.get('reason','Initial scan in progress...'):<30} | Action: {_color(intel.get('action','HOLD'), intel.get('color','white'))}")

            out(_color(" 🧠 GLOBAL MACRO & VOLATILITY ", "blue", True).center(w, "═"), pad=False)
            iv_val = ctx.get("current_iv", 0.0)
            iv_reg = ctx.get("iv_regime", "NORMAL_IV")
            iv_c = "green" if iv_reg == "LOW_IV" else "red" if iv_reg == "HIGH_IV" else "yellow"
            out(f" Implied Vol: {_color(str(iv_val)+'%', iv_c):<20} | IV Regime: {_color(iv_reg, iv_c)}")
            out(f" News Score: {_color(str(round(ctx.get('news_sentiment',0.0),2)), 'cyan'):<21} | Theta Risk: {_color(ctx.get('theta_risk','SAFE'), 'green')}")
            tp = db_stats.get('today_pnl', 0.0)
            out(f" Today's PnL: {_color('Rs '+str(round(tp,2)), 'green' if tp>=0 else 'red'):<20} | Win Rate: {db_stats.get('win_rate',0)}% | Expectancy: {db_stats.get('expectancy',0)}")
            out(f" Growth: {db_stats.get('growth_rate',0)}% | Zone: {db_stats.get('best_confidence_zone','N/A')}")

            active_idx = best_idx or SETTINGS["SYMBOLS"][0]
            if active_idx and amap.get(active_idx):
                bd = amap.get(active_idx, {})
                out(_color(f" 🧱 {active_idx} DECISION ANALYSIS ", "cyan", True).center(w, "═"), pad=False)
                wp = bd.get('ml_prediction', {}).get('win_probability')
                if wp is None or wp == 0: wp = 50.0
                conf_val = bd.get('confidence', {}).get('confidence', 0.0)
                d_act = decision.get("action", "NO-TRADE")
                d_col = "green" if d_act in ("READY", "ACTIVE") else "yellow"
                out(f" Neural Win %: {_color(str(round(wp,1))+'%', 'green' if wp>55 else 'red'):<22} | Tech Conf: {_color(str(round(conf_val,1))+'%', 'cyan')}")
                out(f" Decision: {_color(d_act, d_col, True):<24} | Risk: {_color(decision.get('risk_status','BLOCKED'), d_col)}")
                out(f" SMC FVG: {_color(bd.get('fvg',{}).get('status','NONE'), 'yellow'):<25} | Trend: {bd.get('structure', {}).get('bias', 'SIDEWAYS').upper()}")
                out(f" SMC Liquid: {bd.get('liquidity',{}).get('status','N/A'):<22} | VSA: {bd.get('vsa',{}).get('vsa_signal','Normal')}")

            out(_color(" 🚀 DECISION OUTPUT ", "yellow", True).center(w, "═"), pad=False)
            tgt = decision.get("targets", {}) or {}; opt = decision.get("option_plan", {}) or {}
            out(f" Action: {_color(decision.get('action', 'NO-TRADE'), 'green' if decision.get('action') in ('READY','ACTIVE') else 'yellow', True):<18} | Symbol: {decision.get('symbol', 'N/A')}")
            out(f" Headline: {decision.get('headline', 'N/A')}")
            out(f" Bias/Regime: {decision.get('bias', 'NEUTRAL')} / {decision.get('regime', 'SCANNING'):<18} | Grade: {decision.get('grade', 'N/A')}")
            out(f" Spot: {decision.get('spot', 0)} | Entry: {tgt.get('entry', 'N/A')} | Stop: {tgt.get('stop', 'N/A')} | Target: {tgt.get('target', 'N/A')}")
            out(f" Option Plan: {opt.get('strike', 'N/A')} {opt.get('option_type', '')} | Confidence: {decision.get('confidence', 0)}%")
            out(f" Summary: {str(decision.get('summary', ''))[:w-11]}")

            out(_color(" 🧱 BLOCKERS / WHY NO TRADE ", "red", True).center(w, "═"), pad=False)
            reasons = decision.get("reasons", [])
            if reasons:
                for r in reasons[:3]: out(f" - {r}")
            else: out(" - None")

            out(_color(" 📌 TRADE RATIONALE ", "cyan", True).center(w, "═"), pad=False)
            rationale = decision.get("rationale", [])
            if rationale:
                for r in rationale[:3]: out(f" - {r}")
            else: out(" - Scanning...")

            out(_color(" 🚀 EXECUTION STATUS (Arrows: Select, Enter: Exit, X: All) ", "yellow", True).center(w, "═"), pad=False)
            if execution_engine.positions:
                for p in execution_engine.positions:
                    pnl = round(p.get('floating_pnl',0),2)
                    pbc = "green" if pnl > 0 else "red" if pnl < 0 else "white"
                    
                    # Detailed fields
                    entry = p.get('entry', 0)
                    live = p.get('current_price', entry)
                    target = p.get('target', 0)
                    stop = p.get('stop', 0)
                    opt_type = p.get('option_type', '')
                    
                    # Calculate Progress %
                    try:
                        total_move = target - entry
                        current_move = live - entry
                        progress_pct = (current_move / total_move) * 100 if total_move != 0 else 0
                    except: progress_pct = 0
                    
                    # Progress Bar Color Logic (Dynamic)
                    bar_width = 30
                    filled_chars = int(max(0, min(100, abs(progress_pct))) / (100/bar_width))
                    
                    # If profit: Green bar. If loss: Red bar.
                    bar_color = "green" if pnl > 0 else "red" if pnl < 0 else "white"
                    filled_bar = _color("█" * filled_chars, bar_color)
                    empty_bar = "░" * (bar_width - filled_chars)
                    
                    # Live Price Tick Effect
                    tick_sym = _color("▲", "green") if live >= entry else _color("▼", "red")
                    
                    lots = p.get('lots', 1)
                    qty = p.get('total_qty', 0)

                    out(f" > {p['index']} {p.get('strike')} {opt_type:<8} | Lots: {lots} ({qty} Qty) | Entry: {round(entry,2)}")
                    out(f"   Live: {tick_sym} {_color(round(live,2), pbc):<12} | Target: {round(target,2):<12} | SL: {round(stop,2)}")
                    out(f"   PnL: {_color('Rs '+str(pnl), pbc):<18} | Progress: [{filled_bar}{empty_bar}] {round(progress_pct, 1)}%")
                    out("-" * w, pad=False)
            else: 
                out(_color(f" [ {decision.get('action', 'NO-TRADE')} | {str(decision.get('headline')).upper()[:40]} ] ", "white"))

            out(_color(" 📋 RECENT SYSTEM EVENTS ", "blue", True).center(w, "═"), pad=False)
            for log in recent_logs: out(f" {log}")
            out(_color(" 🤖 AI BRAIN ACTIVITY (AUTONOMOUS) ", "magenta", True).center(w, "═"), pad=False)
            for log in recent_ai_logs: out(f" {log}")

            news_list = ctx.get("news_items", [])
            current_news = news_list[int(time.time()/5)%len(news_list)]["text"] if news_list else "Fetching live news..."
            out(_color(" 🗞️ AI NEWS TICKER ", "yellow", True).center(w, "═"), pad=False)
            out(f" {str(current_news)[:w-5]}...")
            out(f" {_color('[Press A to EXIT ALL TRADES]', 'red', True).center(w)}")

            out(_color(" 🛡️ RISK & ACCOUNT ", "blue", True).center(w, "═"), pad=False)
            cpu, ram = ("N/A", "N/A")
            if HAS_PSUTIL: cpu, ram = f"{psutil.cpu_percent()}%", f"{psutil.virtual_memory().percent}%"
            out(f" Equity: Rs {round(execution_engine.total_equity,0):<15} | Drawdown: {db_stats.get('max_drawdown',0)}% | Scans: {ctx.get('scan_count',0)}")
            out(f" CPU/RAM: {cpu} / {ram}{' ':<10} | Uptime: {str(ist_now-boot_time).split('.')[0]:<15}")
            
            sys.stdout.write("".join(f)); sys.stdout.flush(); time.sleep(1)
        except Exception as e: os.system('cls' if os.name == 'nt' else 'clear'); print(f"UI Error: {e}"); time.sleep(2)

@contextlib.contextmanager
def silence_stdout():
    new_target = open(os.devnull, "w"); old_stdout = sys.stdout; old_stderr = sys.stderr
    sys.stdout = new_target; sys.stderr = new_target
    try: yield
    finally: sys.stdout = old_stdout; sys.stderr = old_stderr

if __name__ == "__main__":
    try: run()
    except KeyboardInterrupt: sys.stdout.write(ANSI["show_cursor"] + "\n👋 Stopped.\n")
    except Exception:
        with open("crash_report.log", "a") as f: f.write(f"\n--- CRASH: {datetime.now()} ---\n" + traceback.format_exc())
        traceback.print_exc(); sys.exit(1)
