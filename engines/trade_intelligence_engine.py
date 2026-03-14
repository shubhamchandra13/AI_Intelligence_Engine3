# ============================================================
# 🧠 TRADE INTELLIGENCE ENGINE – INSTITUTIONAL VERSION v3
# Advanced Statistical Brain for Adaptive AI
# + CACHE + SAFE GETTER
# + REGIME / IV / TIME / RISK ANALYTICS ADDED
# NOTHING REMOVED
# ============================================================

import sqlite3
import pandas as pd
import numpy as np
import math
import os


class TradeIntelligenceEngine:

    def __init__(self, db_path="database/trades.db"):
        self.db_path = db_path
        self.stats_cache = {}
        self.local_stats = {} # Standalone Truth
        self.hive_stats = {}  # Collective Wisdom
        # 🔥 Hive Mind Config
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.hive_db_paths = []

    # ============================================================
    # 🧬 HIVE MIND: FIND OTHER DATABASES
    # ============================================================

    def find_external_databases(self):
        """
        Scans the parent directory for other AI engines and their databases.
        """
        paths = []
        try:
            parent_dir = os.path.dirname(self.base_dir)
            if os.path.exists(parent_dir):
                for folder in os.listdir(parent_dir):
                    if folder.startswith("AI_") and folder != os.path.basename(self.base_dir):
                        db_file = os.path.join(parent_dir, folder, "database", "trades.db")
                        if os.path.exists(db_file):
                            paths.append(db_file)
        except Exception as e:
            print(f"⚠️ Hive Mind Discovery Error: {e}")
        
        self.hive_db_paths = paths
        return paths

    # ============================================================
    # LOAD DATA (AGGREGATED)
    # ============================================================

    def load_trades(self, mode="ALL"):
        """
        Loads trades. 
        Modes: 'LOCAL' (Only this engine), 'ALL' (Hive Mind)
        """
        all_dfs = []
        
        # Load local
        try:
            conn = sqlite3.connect(self.db_path)
            local_df = pd.read_sql_query("SELECT * FROM trades", conn)
            conn.close()
            if not local_df.empty:
                all_dfs.append(local_df)
        except: pass

        if mode == "LOCAL":
            return all_dfs[0] if all_dfs else pd.DataFrame()

        # Load Hive Mind
        self.find_external_databases()
        for path in self.hive_db_paths:
            try:
                conn = sqlite3.connect(path)
                df = pd.read_sql_query("SELECT * FROM trades", conn)
                conn.close()
                if not df.empty:
                    df["hive_source"] = os.path.basename(os.path.dirname(os.path.dirname(path)))
                    all_dfs.append(df)
            except: continue

        if not all_dfs:
            return pd.DataFrame()

        return pd.concat(all_dfs, ignore_index=True)

    # ============================================================
    # REFRESH CACHE
    # ============================================================

    def refresh(self):
        """
        Refreshes both local and hive stats independently.
        """
        # 1. Standalone Truth
        local_df = self.load_trades(mode="LOCAL")
        self.local_stats = self._calculate_metrics(local_df) if not local_df.empty else {}

        # 2. Hive Mind Aggregation
        combined_df = self.load_trades(mode="ALL")
        self.hive_stats = self._calculate_metrics(combined_df) if not combined_df.empty else {}

        # 3. Default cache (Local prioritized, Hive as context)
        if self.local_stats:
            self.stats_cache = self.local_stats.copy()
            self.stats_cache["hive_sync"] = True if self.hive_stats else False
            self.stats_cache["hive_trades"] = self.hive_stats.get("total_trades", 0)
        else:
            self.stats_cache = self.hive_stats # Fallback if no local trades yet

    def _calculate_metrics(self, df):
        """Original refresh logic abstracted for re-use"""
        total_trades = len(df)
        wins = df[df["pnl"] > 0]
        losses = df[df["pnl"] <= 0]

        win_rate = round(len(wins) / total_trades * 100, 2)
        avg_win = wins["r_multiple"].mean() if not wins.empty else 0
        avg_loss = losses["r_multiple"].mean() if not losses.empty else 0

        expectancy = round(
            (win_rate / 100 * avg_win) +
            ((100 - win_rate) / 100 * avg_loss),
            2
        )

        max_drawdown = self.calculate_drawdown(df)
        growth_rate = self.calculate_growth(df)
        best_confidence_zone = self.confidence_analysis(df)

        return {
            "total_trades": total_trades,
            "win_rate": win_rate,
            "expectancy": expectancy,
            "max_drawdown": max_drawdown,
            "growth_rate": growth_rate,
            "best_confidence_zone": best_confidence_zone,
            "regime_stats": self.regime_analysis(df),
            "iv_stats": self.iv_analysis(df),
            "probability_model": self.probability_model(df)
        }

    # ============================================================
    # SAFE GETTER
    # ============================================================

    def get_basic_stats(self):
        return self.stats_cache

    # ============================================================
    # ORIGINAL ANALYZE METHOD (UNCHANGED)
    # ============================================================

    def analyze(self):

        self.refresh()

        if not self.stats_cache:
            print("\n📊 No trades available for intelligence analysis.")
            return None

        print("\n" + "═" * 80)
        print("🧠 AI TRADE INTELLIGENCE REPORT")
        print("═" * 80)

        for k, v in self.stats_cache.items():
            print(f"{k} ➜ {v}")

        print("═" * 80)

        return self.stats_cache

    # ============================================================
    # DRAW DOWN
    # ============================================================

    def calculate_drawdown(self, df):
        equity = df["capital_after"]
        peak = equity.cummax()
        drawdown = (equity - peak) / peak * 100
        return round(drawdown.min(), 2)

    # ============================================================
    # CAPITAL GROWTH
    # ============================================================

    def calculate_growth(self, df):
        start_cap = df["capital_before"].iloc[0]
        end_cap = df["capital_after"].iloc[-1]
        growth = ((end_cap - start_cap) / start_cap) * 100
        return round(growth, 2)

    # ============================================================
    # CONFIDENCE ANALYSIS (UNCHANGED)
    # ============================================================

    def confidence_analysis(self, df):

        if "confidence" not in df.columns:
            return "No Data"

        df["conf_bucket"] = pd.cut(
            df["confidence"],
            bins=[0, 70, 75, 80, 85, 100],
            labels=["<70", "70-75", "75-80", "80-85", "85+"]
        )

        bucket_perf = df.groupby("conf_bucket", observed=False)["pnl"].mean()

        if bucket_perf.empty:
            return "Not enough data"

        return bucket_perf.idxmax()

    # ============================================================
    # NEW ANALYTICS METHODS
    # ============================================================

    def regime_analysis(self, df):
        if "regime" not in df.columns:
            return {}
        return df.groupby("regime")["pnl"].mean().to_dict()

    def iv_analysis(self, df):
        if "iv_regime" not in df.columns:
            return {}
        return df.groupby("iv_regime")["pnl"].mean().to_dict()

    def time_analysis(self, df):
        if "entry_time" not in df.columns:
            return {}
        df["hour"] = pd.to_datetime(df["entry_time"], errors="coerce").dt.hour
        return df.groupby("hour")["pnl"].mean().to_dict()

    def risk_efficiency(self, df):
        if "risk_used" not in df.columns:
            return {}
        return df.groupby("risk_used")["pnl"].mean().to_dict()

    def duration_analysis(self, df):
        if "trade_duration" not in df.columns:
            return {}
        return {
            "avg_duration": round(df["trade_duration"].mean(), 2),
            "max_duration": round(df["trade_duration"].max(), 2),
            "min_duration": round(df["trade_duration"].min(), 2)
        }

    # ============================================================
    # PROBABILITY ENGINE (CONFIDENCE + REGIME + IV)
    # ============================================================

    def _confidence_bucket(self, confidence):
        if confidence is None:
            return "UNKNOWN"
        if confidence < 30:
            return "<30"
        if confidence < 40:
            return "30-40"
        if confidence < 50:
            return "40-50"
        if confidence < 60:
            return "50-60"
        if confidence < 70:
            return "60-70"
        if confidence < 80:
            return "70-80"
        return "80+"

    def _with_profit_flag(self, df):
        data = df.copy()
        data["is_profit"] = (data["pnl"] > 0).astype(int)
        data["conf_bucket"] = data["confidence"].apply(self._confidence_bucket)
        return data

    def _safe_probability_stats(self, sample_df, global_win_rate, global_expectancy, prior_n=20):
        if sample_df is None or sample_df.empty:
            return None

        n = len(sample_df)
        wins = int(sample_df["is_profit"].sum())
        raw_win_rate = (wins / n) * 100
        raw_expectancy = sample_df["r_multiple"].mean() if "r_multiple" in sample_df.columns else 0
        avg_pnl = sample_df["pnl"].mean()

        prior_wins = (global_win_rate / 100.0) * prior_n
        smoothed_win_rate = ((wins + prior_wins) / (n + prior_n)) * 100
        smoothed_expectancy = ((raw_expectancy * n) + (global_expectancy * prior_n)) / (n + prior_n)

        confidence_band = min(99.0, 40 + (math.sqrt(n) * 8))

        return {
            "sample_size": n,
            "win_rate_raw": round(raw_win_rate, 2),
            "win_probability": round(smoothed_win_rate, 2),
            "expectancy_r": round(float(smoothed_expectancy), 3),
            "avg_pnl": round(float(avg_pnl), 2),
            "model_confidence": round(confidence_band, 2)
        }

    def probability_model(self, df):
        required = {"pnl", "confidence"}
        if not required.issubset(set(df.columns)):
            return {}

        data = self._with_profit_flag(df)

        global_win_rate = data["is_profit"].mean() * 100
        global_expectancy = data["r_multiple"].mean() if "r_multiple" in data.columns else 0

        by_confidence = {}
        for bucket, grp in data.groupby("conf_bucket", observed=False):
            stats = self._safe_probability_stats(grp, global_win_rate, global_expectancy)
            if stats:
                by_confidence[bucket] = stats

        by_regime = {}
        if "regime" in data.columns:
            for regime_name, grp in data.groupby("regime"):
                stats = self._safe_probability_stats(grp, global_win_rate, global_expectancy)
                if stats:
                    by_regime[regime_name] = stats

        by_iv = {}
        if "iv_regime" in data.columns:
            for iv_regime, grp in data.groupby("iv_regime"):
                stats = self._safe_probability_stats(grp, global_win_rate, global_expectancy)
                if stats:
                    by_iv[iv_regime] = stats

        return {
            "global": {
                "sample_size": int(len(data)),
                "win_probability": round(float(global_win_rate), 2),
                "expectancy_r": round(float(global_expectancy), 3)
            },
            "by_confidence": by_confidence,
            "by_regime": by_regime,
            "by_iv_regime": by_iv
        }

    def estimate_setup_probability(self, confidence, regime=None, iv_regime=None):
        df = self.load_trades()

        if df.empty or "pnl" not in df.columns or "confidence" not in df.columns:
            return {
                "source": "no_data",
                "sample_size": 0,
                "win_probability": None,
                "expectancy_r": None,
                "avg_pnl": None,
                "model_confidence": 0
            }

        if "r_multiple" not in df.columns:
            df["r_multiple"] = 0

        data = self._with_profit_flag(df)
        global_win_rate = data["is_profit"].mean() * 100
        global_expectancy = data["r_multiple"].mean()
        conf_bucket = self._confidence_bucket(confidence)

        regime_name = None
        if isinstance(regime, dict):
            regime_name = regime.get("regime")
        elif isinstance(regime, str):
            regime_name = regime

        if iv_regime is None:
            iv_regime = "UNKNOWN"

        candidates = []

        if "regime" in data.columns and "iv_regime" in data.columns and regime_name:
            candidates.append((
                "conf+regime+iv",
                data[
                    (data["conf_bucket"] == conf_bucket) &
                    (data["regime"] == regime_name) &
                    (data["iv_regime"] == iv_regime)
                ]
            ))

        if "regime" in data.columns and regime_name:
            candidates.append((
                "conf+regime",
                data[
                    (data["conf_bucket"] == conf_bucket) &
                    (data["regime"] == regime_name)
                ]
            ))

        candidates.append((
            "confidence_bucket",
            data[data["conf_bucket"] == conf_bucket]
        ))

        if "regime" in data.columns and regime_name:
            candidates.append((
                "regime",
                data[data["regime"] == regime_name]
            ))

        candidates.append(("global", data))

        for source, grp in candidates:
            stats = self._safe_probability_stats(grp, global_win_rate, global_expectancy)
            if stats and stats["sample_size"] > 0:
                stats["source"] = source
                stats["confidence_bucket"] = conf_bucket
                stats["regime"] = regime_name
                stats["iv_regime"] = iv_regime
                return stats

        return {
            "source": "no_match",
            "sample_size": 0,
            "win_probability": round(float(global_win_rate), 2),
            "expectancy_r": round(float(global_expectancy), 3),
            "avg_pnl": None,
            "model_confidence": 0,
            "confidence_bucket": conf_bucket,
            "regime": regime_name,
            "iv_regime": iv_regime
        }
