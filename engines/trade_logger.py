# ============================================================
# 📊 TRADE LOGGER – AI READY VERSION (AUTO MIGRATION ENABLED)
# Stores Complete Trade State for Intelligence Layer
# ============================================================

import sqlite3
import os
import json


class TradeLogger:

    def __init__(self, db_path="database/trades.db"):

        os.makedirs("database", exist_ok=True)
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.rejection_log_path = "database/trade_rejections.log"
        self.rejection_history = {} # Prevent spamming logs for same reason

        self.create_table()
        self.create_feature_store_table()
        self.auto_migrate_schema()   # 🔥 NEW

    def log_rejection(self, symbol, reason, confidence):
        """
        Audit Item #9: Persistent log of trade rejection reasons.
        """
        from datetime import datetime
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Only log if reason changed or significant time passed (avoid spam)
        last_log = self.rejection_history.get(symbol, {}).get("reason")
        if last_log == reason:
            return

        with open(self.rejection_log_path, "a") as f:
            f.write(f"[{now}] REJECTED {symbol} | Conf: {round(confidence,1)}% | Reason: {reason}\n")
        
        self.rejection_history[symbol] = {"reason": reason, "time": now}

    # ============================================================
    # CREATE TABLE
    # ============================================================

    def create_table(self):

        query = """
        CREATE TABLE IF NOT EXISTS trades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            index_name TEXT,
            direction TEXT,
            entry_price REAL,
            exit_price REAL,
            pnl REAL,
            r_multiple REAL,
            confidence REAL,
            risk_percent REAL,
            capital_before REAL,
            capital_after REAL,
            exit_reason TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        """

        self.conn.execute(query)
        self.conn.commit()

    def create_feature_store_table(self):

        query = """
        CREATE TABLE IF NOT EXISTS ai_feature_store (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            trade_id INTEGER,
            index_name TEXT,
            direction TEXT,
            regime TEXT,
            iv_regime TEXT,
            confidence REAL,
            risk_used REAL,
            target_used REAL,
            indicator_score REAL,
            indicator_confluence REAL,
            ai_quality_score REAL,
            ai_uncertainty_score REAL,
            ai_risk_multiplier REAL,
            stat_win_probability REAL,
            ml_win_probability REAL,
            meta_quality_probability REAL,
            ml_model_version TEXT,
            raw_features_json TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        """

        self.conn.execute(query)
        self.conn.commit()

    # ============================================================
    # AUTO SCHEMA MIGRATION (NEW – SAFE)
    # ============================================================

    def auto_migrate_schema(self):

        new_columns = {
            "regime": "TEXT",
            "iv_regime": "TEXT",
            "theta_risk": "TEXT",
            "risk_used": "REAL",
            "target_used": "REAL",
            "entry_time": "TEXT",
            "exit_time": "TEXT",
            "trade_duration": "REAL",
            "setup_json": "TEXT",
            "trade_mode": "TEXT",
            "session_type": "TEXT",
            "strategy_version": "TEXT",
            "config_version": "TEXT",
            "replay_batch_id": "TEXT",
            "market_regime": "TEXT",
            "confidence_bucket": "TEXT",
            "data_source": "TEXT"
        }

        cursor = self.conn.cursor()
        cursor.execute("PRAGMA table_info(trades)")
        existing_columns = [col[1] for col in cursor.fetchall()]

        for column, dtype in new_columns.items():
            if column not in existing_columns:
                cursor.execute(f"ALTER TABLE trades ADD COLUMN {column} {dtype}")
                print(f"Added new column: {column}")

        self.conn.commit()
        self.auto_migrate_feature_store_schema()

    def auto_migrate_feature_store_schema(self):

        new_columns = {
            "structure_bias": "TEXT",
            "relative_score": "REAL",
            "oi_bias": "TEXT",
            "oi_pcr": "REAL",
            "oi_call_wall": "REAL",
            "oi_put_wall": "REAL",
            "theta_minutes_to_expiry": "REAL",
            "theta_decay_score": "REAL",
            "iv_score": "REAL",
            "option_strike": "REAL",
            "option_type": "TEXT",
            "option_ltp": "REAL",
            "option_bid": "REAL",
            "option_ask": "REAL",
            "spread_pct": "REAL",
            "estimated_slippage_pct": "REAL",
            "liquidity_score": "REAL",
            "portfolio_heat_pct": "REAL",
            "allocation_weight": "REAL"
        }

        cursor = self.conn.cursor()
        cursor.execute("PRAGMA table_info(ai_feature_store)")
        existing_columns = [col[1] for col in cursor.fetchall()]

        for column, dtype in new_columns.items():
            if column not in existing_columns:
                cursor.execute(f"ALTER TABLE ai_feature_store ADD COLUMN {column} {dtype}")
                print(f"Added new ai_feature_store column: {column}")

        self.conn.commit()

    def _safe_json_load(self, raw):
        if not raw:
            return {}
        if isinstance(raw, dict):
            return raw
        try:
            return json.loads(raw)
        except Exception:
            return {}

    def log_feature_store(self, trade_id, trade_data):
        try:
            setup = self._safe_json_load(trade_data.get("setup_json"))
            indicator = setup.get("indicator_stack") or {}
            ai_decision = setup.get("ai_decision") or {}
            stat_prob = setup.get("stat_probability") or {}
            ml_prob = setup.get("ml_probability") or {}
            meta_label = setup.get("meta_label") or {}
            oi_data = setup.get("oi_data") or {}
            theta_data = setup.get("theta_data") or {}
            iv_data = setup.get("iv_data") or {}
            selected_option = setup.get("selected_option") or {}
            execution_quality = setup.get("execution_quality") or {}
            portfolio_allocation = setup.get("portfolio_allocation") or {}

            query = """
            INSERT INTO ai_feature_store (
                trade_id, index_name, direction, regime, iv_regime, confidence, risk_used, target_used,
                indicator_score, indicator_confluence, ai_quality_score, ai_uncertainty_score, ai_risk_multiplier,
                stat_win_probability, ml_win_probability, meta_quality_probability, ml_model_version,
                structure_bias, relative_score, oi_bias, oi_pcr, oi_call_wall, oi_put_wall,
                theta_minutes_to_expiry, theta_decay_score, iv_score, option_strike, option_type,
                option_ltp, option_bid, option_ask, spread_pct, estimated_slippage_pct,
                liquidity_score, portfolio_heat_pct, allocation_weight, raw_features_json
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """

            values = (
                trade_id,
                trade_data.get("index"),
                trade_data.get("direction"),
                trade_data.get("regime"),
                trade_data.get("iv_regime"),
                trade_data.get("confidence"),
                trade_data.get("risk_used"),
                trade_data.get("target_used"),
                indicator.get("score"),
                indicator.get("confluence"),
                ai_decision.get("quality_score"),
                ai_decision.get("uncertainty_score"),
                ai_decision.get("risk_multiplier"),
                stat_prob.get("win_probability"),
                ml_prob.get("win_probability"),
                meta_label.get("take_quality_probability"),
                ml_prob.get("model_version"),
                setup.get("structure_bias"),
                setup.get("relative_score"),
                oi_data.get("bias"),
                oi_data.get("pcr"),
                oi_data.get("call_wall"),
                oi_data.get("put_wall"),
                theta_data.get("minutes_to_expiry"),
                theta_data.get("decay_score"),
                iv_data.get("iv_score"),
                selected_option.get("strike"),
                selected_option.get("option_type"),
                execution_quality.get("ltp"),
                execution_quality.get("bid"),
                execution_quality.get("ask"),
                execution_quality.get("spread_pct"),
                execution_quality.get("estimated_slippage_pct"),
                execution_quality.get("liquidity_score"),
                portfolio_allocation.get("current_symbol_exposure_pct"),
                (portfolio_allocation.get("symbol_weights") or {}).get(trade_data.get("index")),
                json.dumps(setup, ensure_ascii=True, default=str),
            )

            self.conn.execute(query, values)
            self.conn.commit()
        except Exception as e:
            print(f"❌ Feature Store Error: {e}")

    # ============================================================
    # LOG CLOSED TRADE
    # ============================================================

    def log_trade(self, trade_data):
        try:
            query = """
            INSERT INTO trades (
                index_name, direction, entry_price, exit_price, pnl, r_multiple, confidence,
                risk_percent, capital_before, capital_after, exit_reason, regime, iv_regime,
                theta_risk, risk_used, target_used, entry_time, exit_time, trade_duration, setup_json,
                trade_mode, session_type, strategy_version, config_version, replay_batch_id,
                market_regime, confidence_bucket, data_source
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """

            values = (
                trade_data.get("index"),
                trade_data.get("direction"),
                trade_data.get("entry_price"),
                trade_data.get("exit_price"),
                trade_data.get("pnl"),
                trade_data.get("r_multiple"),
                trade_data.get("confidence"),
                trade_data.get("risk_percent"),
                trade_data.get("capital_before"),
                trade_data.get("capital_after"),
                trade_data.get("exit_reason"),
                trade_data.get("regime"),
                trade_data.get("iv_regime"),
                trade_data.get("theta_risk"),
                trade_data.get("risk_used"),
                trade_data.get("target_used"),
                trade_data.get("entry_time"),
                trade_data.get("exit_time"),
                trade_data.get("trade_duration"),
                trade_data.get("setup_json"),
                trade_data.get("trade_mode", "LIVE_PAPER"),
                trade_data.get("session_type", "INTRADAY"),
                trade_data.get("strategy_version", "1.0"),
                trade_data.get("config_version", "1.0"),
                trade_data.get("replay_batch_id", None),
                trade_data.get("market_regime", trade_data.get("regime", "UNKNOWN")),
                trade_data.get("confidence_bucket", f"{int(trade_data.get('confidence', 0)//10)*10}s"),
                trade_data.get("data_source", "UPSTOX")
            )

            cursor = self.conn.execute(query, values)
            self.conn.commit()
            trade_id = cursor.lastrowid
            self.log_feature_store(trade_id, trade_data)
            print(f"✅ Trade {trade_id} Logged (AI Intelligence Ready)")
        except Exception as e:
            print(f"❌ Trade Logging Error: {e}")
