import pandas as pd
from datetime import datetime
import time

class HistoricalReplayEngine:
    """
    Replays historical candles chronologically to simulate a live market environment.
    Uses the same StrategyEngine as live mode to ensure consistency.
    """
    def __init__(self, strategy_engine, execution_engine, db_logger):
        self.strategy_engine = strategy_engine
        self.execution_engine = execution_engine
        self.db_logger = db_logger
        self.is_running = False
        self.current_time = None
        self.replay_data = {} # {symbol: pd.DataFrame}
        self.batch_id = f"REPLAY_{int(time.time())}"

    def load_data(self, data_fetcher, symbols, start_date, end_date, interval="1minute"):
        """
        Loads historical data for the given symbols and date range.
        If start_date is None, loads last ~90 days by default to simulate recent history.
        """
        if not end_date:
            end_date = datetime.now()
        if not start_date:
            from config import SETTINGS
            lookback_months = SETTINGS.get("REPLAY_LOOKBACK_MONTHS", 3)
            start_date = end_date - pd.Timedelta(days=30 * lookback_months) # Default to REPLAY_LOOKBACK_MONTHS
            
        print(f"Loading historical data from {start_date.date()} to {end_date.date()}...")

        for sym in symbols:
            print(f"Fetching chunks for {sym}...")
            # Fetch in chunks of 5 days (Upstox intraday history API limit)
            current_end = end_date
            all_dfs = []
            
            while current_end > start_date:
                current_start = max(start_date, current_end - pd.Timedelta(days=5))
                
                # We need to hit the Upstox API directly for precise historical windows
                # The generic get_candles only looks back ~5 days max
                from config import SETTINGS
                instrument_key = SETTINGS.get("INSTRUMENT_KEYS", {}).get(sym)
                if not instrument_key: 
                    break
                    
                to_date_str = current_end.strftime("%Y-%m-%d")
                from_date_str = current_start.strftime("%Y-%m-%d")
                
                from core.data_fetcher import BASE_URL
                url_hist = f"{BASE_URL}/historical-candle/{instrument_key}/{interval}/{to_date_str}/{from_date_str}"
                
                try:
                    import requests
                    resp = requests.get(url_hist, headers=data_fetcher._get_headers())
                    data = resp.json()
                    if data.get("status") == "success":
                        candles = data.get("data", {}).get("candles", [])
                        if candles:
                            chunk_df = pd.DataFrame(candles)
                            all_dfs.append(chunk_df)
                except Exception as e:
                    print(f"Error fetching chunk: {e}")
                    
                current_end = current_start - pd.Timedelta(days=1)
                time.sleep(0.5) # Rate limit protection

            if all_dfs:
                combined_df = pd.concat(all_dfs, ignore_index=True)
                combined_df = combined_df.drop_duplicates(subset=0).sort_values(0)
                
                if len(combined_df.columns) >= 6:
                    combined_df = combined_df.iloc[:, :6]
                    combined_df.columns = ["timestamp", "open", "high", "low", "close", "volume"]
                    combined_df["timestamp"] = pd.to_datetime(combined_df["timestamp"])
                    combined_df.set_index('timestamp', inplace=True)
                    combined_df.sort_index(inplace=True)
                    
                    self.replay_data[sym] = combined_df
                    print(f"Loaded {len(combined_df)} candles for {sym}.")
            else:
                print(f"Warning: No data loaded for {sym}")
        
        return len(self.replay_data) > 0

    def start_replay(self):
        self.is_running = True
        
        # Find common timeline
        common_times = set()
        for sym, df in self.replay_data.items():
            if not common_times:
                common_times = set(df.index)
            else:
                common_times = common_times.intersection(set(df.index))
        
        timeline = sorted(list(common_times))
        
        print(f"Starting historical replay: {len(timeline)} steps.")

        for current_time in timeline:
            if not self.is_running:
                break
            
            self.current_time = current_time
            self.step()
            
        print("Replay completed.")
        self.generate_report()

    def stop_replay(self):
        self.is_running = False

    def step(self):
        """
        Executes a single step in the historical replay.
        """
        market_context = {
            "iv_data": {"current_iv": 15.0, "iv_regime": "NORMAL_IV"},
            "sentiment": 0.0,
            "ofi_data": {}
        }
        
        best_symbol = None
        best_decision = None
        highest_conf = 0
        
        # 1. Analyze all symbols at current step
        for sym, df in self.replay_data.items():
            # Slice dataframe up to current time
            step_df = df.loc[:self.current_time]
            if len(step_df) < 50: # Need minimum data for indicators
                continue
                
            current_spot = step_df.iloc[-1]['close']
            market_context["other_df"] = self.replay_data.get("BANKNIFTY" if sym == "NIFTY" else "NIFTY").loc[:self.current_time] if "NIFTY" in self.replay_data else None

            # Run strategy engine
            analysis = self.strategy_engine.analyze_symbol(sym, step_df, current_spot, market_context)
            if analysis:
                decision = self.strategy_engine.make_decision(analysis)
                
                if decision["action"] == "READY" and decision["confidence"] > highest_conf:
                    highest_conf = decision["confidence"]
                    best_symbol = sym
                    best_decision = decision
                    best_analysis = analysis
                    
        # 2. Execute trade if a valid setup is found and no current position
        if best_symbol and not self.execution_engine.positions:
            print(f"[{self.current_time}] Replay Trade Triggered: {best_symbol} @ Conf {highest_conf}%")
            direction = "BULLISH" if best_decision["bias"].upper() == "BULLISH" else "BEARISH"
            opt_type = "CE" if direction == "BULLISH" else "PE"
            
            # Simulated Execution
            self.execution_engine.enter_trade(
                index=best_symbol,
                direction=direction,
                price=best_analysis["spot"],
                confidence=best_decision["confidence"],
                df=step_df,
                dynamic_risk=best_analysis["risk"],
                target_multiplier=1.5,
                ladder_strikes=[(0, opt_type, "SIM_KEY", 1.0)] # Dummy strike for sim
            )
            
        # 3. Update PnL & Check Exits
        if self.execution_engine.positions:
            price_map = {}
            for p in self.execution_engine.positions:
                sym = p['index']
                if sym in self.replay_data:
                    step_df = self.replay_data[sym].loc[:self.current_time]
                    current_spot = step_df.iloc[-1]['close']
                    
                    # For simple replay, we simulate Option PnL matching exactly with Spot Points (Delta 1.0)
                    # To calculate accurate PnL, we find the difference in spot and apply to entry
                    entry_spot = p.get('entry_spot', current_spot) # Fallback if not tracked
                    
                    if p['direction'] == 'BUY':
                        simulated_ltp = p['entry'] + (current_spot - entry_spot)
                    else:
                        simulated_ltp = p['entry'] + (entry_spot - current_spot)
                        
                    price_map[p.get('instrument_key')] = simulated_ltp

            if price_map:
                self.execution_engine.update_floating_pnl(price_map)
                closed = self.execution_engine.check_exit(price_map, df_map={})
                if closed:
                    print(f"[{self.current_time}] Replay Exit: {closed['index']} at {closed['exit_price']} PnL: {closed['pnl']}")
                    # Log trade
                    self._log_replay_trade(closed, best_decision)

    def _log_replay_trade(self, trade_data, decision_data):
        """
        Logs a simulated trade with replay tags.
        """
        log_data = {
            "index": trade_data.get("index"),
            "direction": trade_data.get("direction", "UNKNOWN"),
            "entry_price": trade_data.get("entry_price", 0.0),
            "exit_price": trade_data.get("exit_price", 0.0),
            "pnl": trade_data.get("pnl", 0.0),
            "r_multiple": trade_data.get("r_multiple", 0.0),
            "confidence": decision_data.get("confidence", 0.0) if decision_data else 0.0,
            "risk_percent": trade_data.get("risk_percent", 0.0),
            "capital_before": trade_data.get("capital_before", 0.0),
            "capital_after": trade_data.get("capital_after", 0.0),
            "exit_reason": trade_data.get("reason", "SIMULATED_EXIT"),
            "regime": decision_data.get("regime", "UNKNOWN") if decision_data else "UNKNOWN",
            "iv_regime": trade_data.get("iv_regime", "NORMAL_IV"),
            "theta_risk": trade_data.get("theta_risk", "SAFE"),
            "risk_used": trade_data.get("risk_used", 0.0),
            "target_used": trade_data.get("target_used", 0.0),
            "entry_time": str(trade_data.get("entry_time", self.current_time)),
            "exit_time": str(self.current_time),
            "trade_duration": (self.current_time - pd.to_datetime(trade_data.get("entry_time", self.current_time))).total_seconds() / 60.0 if isinstance(self.current_time, datetime) and "entry_time" in trade_data else 0.0,
            "setup_json": "{}",
            "trade_mode": "HISTORICAL_REPLAY",
            "session_type": "SIMULATED",
            "strategy_version": "1.0",
            "config_version": "1.0",
            "replay_batch_id": self.batch_id,
            "market_regime": decision_data.get("regime", "UNKNOWN") if decision_data else "UNKNOWN",
            "confidence_bucket": f"{int(decision_data.get('confidence', 0)//10)*10}s" if decision_data else "0s",
            "data_source": "SIMULATION"
        }
        self.db_logger.log_trade(log_data)

    def generate_report(self):
        """
        Generates summary statistics for the replay batch and saves it to a file.
        """
        print(f"--- Replay Report (Batch: {self.batch_id}) ---")
        
        # We can fetch the stats directly from the Evaluation Engine
        from engines.evaluation_engine import EvaluationEngine
        eval_engine = EvaluationEngine()
        stats = eval_engine.evaluate_performance(trade_mode="HISTORICAL_REPLAY", replay_batch_id=self.batch_id)
        
        report_content = f"""
=========================================
REPLAY BATCH: {self.batch_id}
=========================================
Total Trades: {stats.get("total_trades", 0)}
Win Rate: {stats.get("win_rate", 0)}%
Expectancy: {stats.get("expectancy", 0)}
Profit Factor: {stats.get("profit_factor", 0)}
Max Drawdown: {stats.get("max_drawdown", 0)}
Net PnL: {stats.get("net_pnl", 0)}
=========================================
        """
        print(report_content)
        
        import os
        report_dir = "reports/replay_reports"
        os.makedirs(report_dir, exist_ok=True)
        report_path = os.path.join(report_dir, f"{self.batch_id}_summary.txt")
        with open(report_path, "w") as f:
            f.write(report_content)
        print(f"Report saved to {report_path}")
