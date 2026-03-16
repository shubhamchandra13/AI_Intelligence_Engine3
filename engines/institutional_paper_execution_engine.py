# ============================================================
# INSTITUTIONAL PAPER EXECUTION ENGINE - PRODUCTION
# Upgraded with partial booking, profit lock, and strike cooldown
# ============================================================

import math
import json
import os
import pandas as pd
from datetime import datetime, timedelta
from engines.trade_logger import TradeLogger
from engines.trade_intelligence_engine import TradeIntelligenceEngine
from engines.safe_notifier import SafeNotifier


class InstitutionalPaperExecutionEngine:

    def __init__(
        self,
        initial_capital=100000,
        partial_profit_trigger_pct=12.0,
        partial_book_fraction=0.5,
        profit_lock_activation_pct=10.0,
        min_profit_lock_pct=5.0,
        trailing_buffer_pct=6.0,
        same_strike_cooldown_minutes=15,
        index_exit_rules=None,
        rl_engine=None,
    ):
        self.rl_engine = rl_engine

        self.initial_capital = initial_capital
        self.capital = self._load_persistent_capital(initial_capital)
        self.locked_capital = 0
        self.floating_pnl = 0

        self.positions = []
        self.last_closed_trade = None

        self.lot_sizes = {
            "NIFTY": 65,
            "BANKNIFTY": 30,
        }

        self.max_exposure_pct = 0.60
        self.min_lot_risk_trigger = 0.10

        self.partial_profit_trigger_pct = float(partial_profit_trigger_pct)
        self.partial_book_fraction = float(partial_book_fraction)
        self.profit_lock_activation_pct = float(profit_lock_activation_pct)
        self.min_profit_lock_pct = float(min_profit_lock_pct)
        self.trailing_buffer_pct = float(trailing_buffer_pct)
        self.same_strike_cooldown_minutes = int(same_strike_cooldown_minutes)
        self.index_exit_rules = index_exit_rules or {}
        self.runtime_index_exit_rules = {}
        self.runtime_profile_name = "BASE"
        self.same_strike_cooldowns = {}
        self.last_trade_results = {} # Track result of each strike

        self.last_regime = None
        self.last_iv_data = None
        self.last_theta_data = None
        self.last_dynamic_risk = None
        self.last_target_multiplier = None
        self.last_market_snapshot = None

        self.trade_logger = TradeLogger()
        self.trade_intelligence = TradeIntelligenceEngine()
        self.notifier = SafeNotifier()

    def _load_persistent_capital(self, default_capital):
        """Loads updated capital from database/account_balance.json if exists."""
        try:
            os.makedirs("database", exist_ok=True)
            path = "database/account_balance.json"
            if os.path.exists(path):
                with open(path, "r") as f:
                    data = json.load(f)
                    return float(data.get("current_capital", default_capital))
        except Exception as e:
            print(f"Error loading persistent capital: {e}")
        return default_capital

    def _save_persistent_capital(self):
        """Saves current_capital to database/account_balance.json."""
        try:
            os.makedirs("database", exist_ok=True)
            path = "database/account_balance.json"
            with open(path, "w") as f:
                json.dump({"current_capital": self.capital, "last_updated": datetime.now().isoformat()}, f)
        except Exception as e:
            print(f"Error saving persistent capital: {e}")

    def force_close_all(self, price_map, reason="Force Exit"):
        """Closes all open positions using provided prices."""
        if not self.positions:
            return []
            
        closed_list = []
        for position in self.positions[:]:
            ik = position.get("instrument_key")
            current = price_map.get(ik)
            if current is None:
                continue

            entry = float(position["entry"])
            qty = int(position["total_qty"])
            pnl = (float(current) - entry) * qty + float(position.get("realized_pnl", 0.0))
            
            capital_used = float(position.get("capital_used", 0))
            self.locked_capital -= capital_used
            self.capital += capital_used + (current - entry) * qty
            self._save_persistent_capital()

            trade_data = {
                "index": position["index"],
                "direction": position["direction"],
                "entry_price": entry,
                "exit_price": current,
                "pnl": pnl,
                "reason": reason,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Log to DB
            self.trade_logger.log_trade({
                **trade_data,
                "r_multiple": round(pnl / (position.get("initial_capital_used", 1) * 0.1), 2),
                "confidence": position["confidence"],
                "exit_time": datetime.utcnow().isoformat(),
                "exit_reason": reason
            })
            
            self.notifier.send(f"🕒 AUTO-SQUAREOFF: {position['index']}\nPnL: Rs{round(pnl,2)} | Reason: {reason}")
            self.positions.remove(position)
            closed_list.append(trade_data)
            
        return closed_list

    def emergency_exit(self, reason="BLACK SWAN DETECTED"):
        """Closes all positions immediately regardless of PnL."""
        if not self.positions:
            return
        
        print(f"!!! EMERGENCY KILL SWITCH TRIGGERED: {reason} !!!")
        for pos in self.positions[:]:
            # We assume current price is exit price for emergency
            entry = float(pos["entry"])
            # In a real scenario, we'd fetch the latest LTP here
            # For now, we use a 1% slippage penalty for emergency exit
            exit_price = entry * 0.99 if pos["direction"] == "BUY" else entry * 1.01
            
            remaining_qty = int(pos.get("total_qty", 0))
            capital_used = float(pos.get("capital_used", 0))
            pnl = (exit_price - entry) * remaining_qty
            
            self.locked_capital -= capital_used
            self.capital += capital_used + pnl
            self._save_persistent_capital()
            
            trade_data = {
                "index": pos["index"],
                "direction": pos["direction"],
                "entry_price": entry,
                "exit_price": exit_price,
                "pnl": pnl,
                "exit_reason": f"EMERGENCY: {reason}",
                "timestamp": datetime.utcnow().isoformat()
            }
            self.trade_logger.log_trade(trade_data)
            self.notifier.send(f"⚠️ EMERGENCY EXIT: {reason}\nPnL: {round(pnl,2)}")
            self.positions.remove(pos)

    def _calculate_chandelier_exit(self, position, current_price, df, multiplier=3.0):
        """Advanced Chandelier Exit using ATR."""
        if df is None or len(df) < 22:
            return position.get("stop")
            
        # Calculate ATR
        high_low = df['high'] - df['low']
        high_cp = abs(df['high'] - df['close'].shift())
        low_cp = abs(df['low'] - df['close'].shift())
        tr = pd.concat([high_low, high_cp, low_cp], axis=1).max(axis=1)
        atr = tr.rolling(window=22).mean().iloc[-1]
        
        if position['direction'] == 'BUY':
            # Highest high since entry
            highest_high = float(position.get("max_price", current_price))
            new_stop = highest_high - (atr * multiplier)
            return max(float(position.get("stop", 0)), new_stop)
        return position.get("stop")

    def enter_laddered_trade(
        self,
        index,
        direction,
        base_price,
        confidence,
        df,
        dynamic_risk,
        target_multiplier,
        strikes_list, # Expects list of (strike, type, key, weight)
    ):
        """Splits trade into multiple strikes (Laddering)."""
        equity = self.get_total_equity()
        total_risk_amount = equity * (dynamic_risk / 100)
        
        for strike_info in strikes_list:
            strike, opt_type, inst_key, weight = strike_info
            strike_risk = total_risk_amount * weight
            
            # Use current LTP for the specific strike if available, else fallback
            price = base_price # Simplified for now
            
            lot_size = self.lot_sizes.get(index, 1)
            lot_value = price * lot_size
            qty_lots = math.floor(strike_risk / lot_value)
            
            if qty_lots > 0:
                self.enter_trade(
                    index=index,
                    direction=direction,
                    price=price,
                    confidence=confidence,
                    df=df,
                    dynamic_risk=(dynamic_risk * weight), # Proportional risk
                    target_multiplier=target_multiplier,
                    strike=strike,
                    option_type=opt_type,
                    instrument_key=inst_key
                )

    def update_context(
        self,
        regime=None,
        iv_data=None,
        theta_data=None,
        dynamic_risk=None,
        target_multiplier=None,
        market_snapshot=None,
    ):
        self.last_regime = regime
        self.last_iv_data = iv_data
        self.last_theta_data = theta_data
        self.last_dynamic_risk = dynamic_risk
        self.last_target_multiplier = target_multiplier
        self.last_market_snapshot = market_snapshot

    @property
    def free_capital(self):
        return self.capital

    @property
    def total_equity(self):
        return self.capital + self.locked_capital + self.floating_pnl

    @property
    def position(self):
        if self.positions:
            return self.positions[0]
        return None

    def get_total_equity(self):
        total_floating = sum(pos.get("floating_pnl", 0) for pos in self.positions)
        self.floating_pnl = total_floating
        return self.capital + self.locked_capital + total_floating

    def _cooldown_key(self, index, strike=None, option_type=None):
        return f"{index}|{strike}|{option_type}"

    def set_runtime_index_exit_rules(self, rules=None, profile_name="BASE"):
        self.runtime_index_exit_rules = rules or {}
        self.runtime_profile_name = profile_name or "BASE"

    def _get_rule(self, index, key, default):
        runtime_rules = self.runtime_index_exit_rules.get(str(index), {})
        if key in runtime_rules:
            return runtime_rules.get(key)
        rules = self.index_exit_rules.get(str(index), {})
        value = rules.get(key, default)
        return value

    def can_enter(self, index, confidence, strike=None, option_type=None):
        # 1. BLOCK IF POSITION ALREADY EXISTS
        if self.positions:
            for pos in self.positions:
                if pos["index"] == index and pos.get("strike") == strike and pos.get("option_type") == option_type:
                    return False, "position_already_exists"
            
            # Also block if we already have 1 position (Institutional Safety)
            if len(self.positions) >= 1:
                return False, "max_concurrent_positions_reached"

        cooldown_mins = int(
            self._get_rule(index, "SAME_STRIKE_COOLDOWN_MINUTES", self.same_strike_cooldown_minutes)
        )
        if cooldown_mins <= 0:
            return True, "cooldown_disabled"
            
        key = self._cooldown_key(index, strike, option_type)
        expiry = self.same_strike_cooldowns.get(key)
        last_result = self.last_trade_results.get(key)

        # --- SMART RE-ENTRY LOGIC ---
        if expiry:
            now = datetime.utcnow()
            if now < expiry:
                # 1. Recovery Mode: If previous trade was a LOSS, allow re-entry if Confidence > 75
                if last_result == "LOSS" and confidence >= 75:
                    return True, "recovery_mode_active"
                
                # 2. Strict Mode: If previous trade was a PROFIT, allow ONLY if Confidence > 85
                if last_result == "PROFIT" and confidence >= 85:
                    return True, "high_conviction_reentry"
                
                # Otherwise, stay in cooldown
                mins = int((expiry - now).total_seconds() / 60) + 1
                return False, f"cooldown_active_{max(1, mins)}m (Prev: {last_result})"

        return True, "ok"

    def _activate_or_update_profit_lock(self, position, current_price):
        idx = position.get("index")
        min_profit_lock_pct = float(
            self._get_rule(idx, "MIN_PROFIT_LOCK_PCT", self.min_profit_lock_pct)
        )
        trailing_buffer_pct = float(
            self._get_rule(idx, "TRAILING_BUFFER_PCT", self.trailing_buffer_pct)
        )
        entry = float(position["entry"])
        max_price = float(position.get("max_price", current_price))
        base_lock = entry * (1.0 + (min_profit_lock_pct / 100.0))
        trail_lock = max_price * (1.0 - (trailing_buffer_pct / 100.0))
        new_lock = max(base_lock, trail_lock)
        prev_lock = position.get("lock_price")
        if prev_lock is None:
            position["lock_price"] = new_lock
        else:
            position["lock_price"] = max(float(prev_lock), new_lock)
        position["profit_lock_active"] = True

    def _attempt_partial_book(self, position, current_price, df=None):
        if position.get("partial_booked"):
            return

        idx = position.get("index")
        entry = float(position["entry"])
        if entry <= 0:
            return

        # 1. Fibonacci-Based Dynamic Trigger
        fib_trigger_met = False
        if df is not None:
            from indicators import calculate_fibonacci_levels
            fib_levels = calculate_fibonacci_levels(df)
            if fib_levels:
                # If price crosses 0.618 Extension or 0.5 Retrace, trigger partial
                target_fib = fib_levels["0.618"] if position["direction"] == "BUY" else fib_levels["0.382"]
                if (position["direction"] == "BUY" and current_price >= target_fib) or \
                   (position["direction"] == "SELL" and current_price <= target_fib):
                    fib_trigger_met = True
                    print(f"🎯 FIBONACCI PARTIAL TRIGGER: Price reached {round(target_fib, 2)}")

        # 2. Percentage-Based Fallback Trigger
        partial_profit_trigger_pct = float(
            self._get_rule(idx, "PARTIAL_PROFIT_TRIGGER_PCT", self.partial_profit_trigger_pct)
        )
        gain_pct = ((float(current_price) - entry) / entry) * 100.0
        
        # Trigger if either Fib or % target met
        if not fib_trigger_met and gain_pct < partial_profit_trigger_pct:
            return

        remaining_qty = int(position.get("total_qty", 0))
        if remaining_qty <= 1:
            position["partial_booked"] = True
            return

        partial_book_fraction = float(
            self._get_rule(idx, "PARTIAL_BOOK_FRACTION", self.partial_book_fraction)
        )
        partial_qty = max(1, int(math.floor(remaining_qty * partial_book_fraction)))
        if partial_qty >= remaining_qty:
            partial_qty = remaining_qty - 1
        if partial_qty <= 0:
            position["partial_booked"] = True
            return

        capital_per_qty = float(position.get("capital_per_qty", 0))
        release_capital = capital_per_qty * partial_qty
        partial_pnl = (float(current_price) - entry) * partial_qty

        self.locked_capital -= release_capital
        self.capital += release_capital + partial_pnl
        self._save_persistent_capital()

        position["total_qty"] = remaining_qty - partial_qty
        position["capital_used"] = max(0.0, float(position.get("capital_used", 0)) - release_capital)
        position["realized_pnl"] = float(position.get("realized_pnl", 0.0)) + partial_pnl
        position["partial_booked"] = True

        self._activate_or_update_profit_lock(position, current_price)
        self.notifier.send(f"✅ PARTIAL PROFIT BOOKED ({idx})\nQty: {partial_qty} | PnL: Rs{round(partial_pnl,2)}")

    def enter_trade(
        self,
        index,
        direction,
        price,
        confidence,
        df,
        dynamic_risk,
        target_multiplier,
        strike=None,
        option_type=None,
        instrument_key=None,
        ladder_strikes=None # NEW: List of (strike, type, key, weight)
    ):
        """
        Executes trade entry with proper Option LTP fetching.
        'price' param is the Index Spot Price (reference only).
        Actual entry uses the Option Premium.
        """
        if price is None or price <= 0:
            return False

        equity = self.get_total_equity()
        total_risk_amount = equity * (dynamic_risk / 100)
        
        # If no ladder, use single strike (Backward Compatible)
        if not ladder_strikes:
            ladder_strikes = [(strike, option_type, instrument_key, 1.0)]

        # Lazy import to avoid circular dependency if any, though top-level is preferred if clean.
        # For safety in this specific engine, we keep it here or move to top if DataFetcher is stable.
        from core.data_fetcher import DataFetcher
        fetcher = DataFetcher()

        success_count = 0
        for s, ot, ik, weight in ladder_strikes:
            if not ik: 
                continue

            # 1. FETCH ACTUAL OPTION PREMIUM (LTP)
            # We explicitly fetch the LTP for the instrument_key. 
            # Passing 'price' (spot) as fallback is dangerous for options, so we default to None.
            if ik == "SIM_KEY":
                option_ltp = price # Simulate option entry at spot price for replay mode
            else:
                option_ltp = fetcher.get_option_ltp(ik)
            
            if not option_ltp or option_ltp <= 0:
                print(f"⚠️ SKIPPING TRADE: Could not fetch LTP for {ik}")
                continue

            strike_risk = total_risk_amount * weight
            lot_size = self.lot_sizes.get(index, 1)
            
            lot_value = option_ltp * lot_size
            
            # Avoid divide by zero
            if lot_value <= 0:
                continue

            qty_lots = math.floor(strike_risk / lot_value)

            # Ensure at least 1 lot if risk allows, or skip
            if qty_lots <= 0:
                # Optional: Force 1 lot if high confidence? 
                # For proper risk mgmt, we stick to math.floor, but let's allow min 1 if equity permits.
                if equity > lot_value: 
                    qty_lots = 1
                else:
                    continue

            required_capital = qty_lots * lot_value
            if required_capital > self.free_capital:
                print(f"⚠️ SKIPPING: Insufficient Capital. Req: {required_capital}, Free: {self.free_capital}")
                continue

            # ================= STOP & TARGET (Based on OPTION PRICE) =================
            # ATR-based or Percentage-based. Defaulting to fixed % for robustness if DF unavailable.
            stop_pct = 0.20  # 20% SL on Option Premium
            target_pct = 0.40 * target_multiplier # Dynamic Target

            stop = option_ltp * (1 - stop_pct)
            target = option_ltp * (1 + target_pct)

            self.capital -= required_capital
            self.locked_capital += required_capital

            entry_time = datetime.utcnow()
            total_qty = qty_lots * lot_size

            position = {
                "index": index,
                "direction": direction,
                "entry": option_ltp, # ✅ CORRECTED: Uses Option LTP
                "lots": qty_lots,
                "lot_size": lot_size,
                "total_qty": total_qty,
                "capital_used": required_capital,
                "initial_capital_used": required_capital,
                "capital_per_qty": (required_capital / total_qty) if total_qty else 0,
                "stop": stop,
                "target": target,
                "confidence": confidence,
                "floating_pnl": 0,
                "entry_time": entry_time,
                "strike": s,
                "option_type": ot,
                "instrument_key": ik,
                "realized_pnl": 0.0,
                "partial_booked": False,
                "profit_lock_active": False,
                "lock_price": None,
                "max_price": float(option_ltp),
                "rl_regime": self.last_regime.get("regime") if isinstance(self.last_regime, dict) else str(self.last_regime),
                "rl_multiplier": getattr(self, "current_rl_mult", 1.0)
            }

            self.positions.append(position)
            success_count += 1
            
            entry_message = self.notifier.format_entry_message(
                position=position,
                snapshot=self.last_market_snapshot,
            )
            self.notifier.send(entry_message)
            print(f"✅ EXECUTED: {index} {s} {ot} @ {option_ltp} | Qty: {total_qty}")

        if success_count > 0:
            self.last_dynamic_risk = dynamic_risk
            self.last_target_multiplier = target_multiplier
            return True
        return False

    def _calculate_dynamic_trailing_sl(self, position, current_price, df):
        """
        AI-Driven Dynamic Trailing: Adjusts SL based on ATR (Volatility)
        If volatility is high, give more room. If low, tighten SL.
        """
        if df is None or len(df) < 20:
            return None

        # Calculate ATR for volatility context
        tr = df['high'] - df['low']
        atr = tr.rolling(14).mean().iloc[-1]
        
        # Dynamic Multiplier: In high trends, we use a tighter 1.5x ATR, in ranging 2.5x ATR
        regime = self.last_regime.get('regime', 'RANGE') if isinstance(self.last_regime, dict) else 'RANGE'
        multiplier = 1.5 if "TREND" in regime else 2.5
        
        # New potential SL
        if position['direction'] == 'BUY': # Long Option
            new_sl = current_price - (atr * multiplier)
            current_sl = position.get('stop', 0)
            # Only move SL UP, never down
            return max(current_sl, new_sl)
        return position.get('stop')

    def check_exit(self, price_map, df_map=None):
        """
        Checks exit conditions for all positions.
        price_map: {instrument_key: current_price}
        df_map: {index_name: dataframe} for technical exits like ATR/Chandelier
        """
        if not self.positions:
            return None

        last_closed_trade = None

        for position in self.positions[:]:
            ik = position.get("instrument_key")
            current = price_map.get(ik)
            if current is None:
                continue
                
            now = datetime.utcnow()
            idx = position.get("index")
            stop = float(position["stop"])
            target = float(position["target"])
            entry = float(position["entry"])
            entry_time = position.get("entry_time")
            exit_reason = None
            
            df = df_map.get(idx) if df_map else None

            position["max_price"] = max(float(position.get("max_price", current)), current)

            # Update Dynamic Trailing SL (Advanced Chandelier)
            dynamic_sl = self._calculate_chandelier_exit(position, current, df)
            if dynamic_sl:
                position["stop"] = dynamic_sl
                stop = dynamic_sl 

            self._attempt_partial_book(position, current, df=df)

            gain_pct = ((current - entry) / entry) * 100.0 if entry > 0 else 0.0
            profit_lock_activation_pct = float(self._get_rule(idx, "PROFIT_LOCK_ACTIVATION_PCT", self.profit_lock_activation_pct))
            
            if gain_pct >= profit_lock_activation_pct:
                self._activate_or_update_profit_lock(position, current)
            elif position.get("profit_lock_active"):
                self._activate_or_update_profit_lock(position, current)

            lock_price = position.get("lock_price")

            if current <= stop:
                exit_reason = "STOP HIT"
            elif lock_price is not None and current <= float(lock_price):
                exit_reason = "PROFIT LOCK HIT"
            elif current >= target:
                exit_reason = "TARGET HIT"
            
            if not exit_reason:
                continue

            remaining_qty = int(position.get("total_qty", 0))
            capital_used = float(position.get("capital_used", 0))
            capital_before = self.capital
            remaining_pnl = (current - entry) * remaining_qty
            total_pnl = float(position.get("realized_pnl", 0.0)) + remaining_pnl

            self.locked_capital -= capital_used
            self.capital += capital_used + remaining_pnl
            self._save_persistent_capital()

            exit_time = now
            duration_minutes = (exit_time - entry_time).total_seconds() / 60 if entry_time else None

            initial_capital_used = float(position.get("initial_capital_used", capital_used))
            risk_unit = initial_capital_used * 0.10 if initial_capital_used > 0 else 1.0
            r_multiple = total_pnl / risk_unit if risk_unit else 0.0

            closed_trade = {
                "index": position["index"],
                "direction": position["direction"],
                "entry_price": entry,
                "exit_price": current,
                "pnl": total_pnl,
                "reason": exit_reason,
            }

            trade_data = {
                "index": position["index"],
                "direction": position["direction"],
                "entry_price": entry,
                "exit_price": current,
                "pnl": total_pnl,
                "r_multiple": round(float(r_multiple), 3),
                "confidence": position["confidence"],
                "risk_percent": self.last_dynamic_risk,
                "capital_before": capital_before,
                "capital_after": self.capital,
                "exit_reason": exit_reason,
                "regime": self.last_regime.get("regime") if isinstance(self.last_regime, dict) else self.last_regime,
                "iv_regime": self.last_iv_data.get("iv_regime") if isinstance(self.last_iv_data, dict) else None,
                "theta_risk": self.last_theta_data.get("theta_risk") if self.last_theta_data else None,
                "entry_time": entry_time.isoformat() if entry_time else None,
                "exit_time": exit_time.isoformat(),
                "trade_duration": duration_minutes,
                "setup_json": json.dumps(self.last_market_snapshot, default=str) if self.last_market_snapshot else None,
            }

            self.trade_logger.log_trade(trade_data)
            self.notifier.send(self.notifier.format_exit_message(trade_data))
            
            # --- 🔥 RL: UPDATE KNOWLEDGE ON EXIT ---
            if self.rl_engine:
                pnl_pct = (total_pnl / initial_capital_used) * 100 if initial_capital_used > 0 else 0
                msg = self.rl_engine.update_knowledge(
                    regime=position.get("rl_regime", "SCANNING"),
                    confidence=position.get("confidence", 0),
                    multiplier=position.get("rl_multiplier", 1.0),
                    pnl_pct=pnl_pct
                )
                print(f"[{datetime.now().strftime('%H:%M:%S')}] 🤖 {msg}")
            
            cooldown_key = self._cooldown_key(position.get("index"), position.get("strike"), position.get("option_type"))
            self.last_trade_results[cooldown_key] = "PROFIT" if total_pnl > 0 else "LOSS"
            
            cooldown_mins = int(self._get_rule(idx, "SAME_STRIKE_COOLDOWN_MINUTES", self.same_strike_cooldown_minutes))
            self.same_strike_cooldowns[cooldown_key] = datetime.utcnow() + timedelta(minutes=max(0, cooldown_mins))

            self.positions.remove(position)
            last_closed_trade = closed_trade
            self.last_closed_trade = closed_trade

        return last_closed_trade

    def get_intelligence_stats(self):
        self.trade_intelligence.refresh()
        return self.trade_intelligence.get_basic_stats()

    def estimate_setup_probability(self, confidence, regime=None, iv_data=None):
        iv_regime = None
        if isinstance(iv_data, dict):
            iv_regime = iv_data.get("iv_regime")
        return self.trade_intelligence.estimate_setup_probability(
            confidence=confidence,
            regime=regime,
            iv_regime=iv_regime,
        )

    def update_floating_pnl(self, price_map):
        """
        Updates PnL for all positions using a map of {instrument_key: price}.
        """
        total_floating = 0
        for position in self.positions:
            ik = position.get("instrument_key")
            current_price = price_map.get(ik)
            
            if current_price is not None:
                entry = float(position["entry"])
                qty = int(position["total_qty"])
                pnl = (float(current_price) - entry) * qty
                position["floating_pnl"] = pnl
                position["current_price"] = current_price
            
            total_floating += position.get("floating_pnl", 0)

        self.floating_pnl = total_floating
        return total_floating

    def print_status(self, price_map=None):

        if price_map:
            if isinstance(price_map, dict):
                self.update_floating_pnl(price_map)
            else:
                # Fallback for single price
                ik = self.position.get("instrument_key") if self.position else None
                if ik:
                    self.update_floating_pnl({ik: price_map})

        print("\nINSTITUTIONAL PORTFOLIO")
        print(f"Initial Capital -> Rs{round(self.initial_capital,2)}")
        print(f"Free Capital -> Rs{round(self.free_capital,2)}")
        print(f"Locked Capital -> Rs{round(self.locked_capital,2)}")
        print(f"Floating PnL -> Rs{round(self.floating_pnl,2)}")
        print(f"Total Equity -> Rs{round(self.total_equity,2)}")
        
        if self.positions:
            print("\n📌 OPEN POSITIONS DETAILS")
            for pos in self.positions:
                cp = pos.get('current_price', 'N/A')
                print(f"Index: {pos['index']} | Instrument: {pos.get('strike')} {pos.get('option_type')}")
                print(f"Entry: {round(pos['entry'],2)} | Live: {cp} | Floating PnL: Rs{round(pos.get('floating_pnl',0),2)}")
                print(f"Stop: {round(pos['stop'],2)} | Target: {round(pos['target'],2)}")
                print("-" * 35)
        print(f"Open Positions -> {len(self.positions)}")
