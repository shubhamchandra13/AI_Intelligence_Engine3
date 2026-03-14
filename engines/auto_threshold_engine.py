import os
import sqlite3
from datetime import datetime

import pandas as pd


from core.runtime_control import upsert_overrides

class AutoThresholdEngine:

    def __init__(
        self,
        db_path="database/trades.db",
        lookback_trades=150,
        min_samples=30,
        tune_interval_seconds=300,
        min_confidence_floor=20,
        max_confidence_ceiling=80,
        confidence_step=5,
        target_win_rate=55.0,
    ):
        self.db_path = db_path
        self.lookback_trades = lookback_trades
        self.min_samples = min_samples
        self.tune_interval_seconds = tune_interval_seconds
        self.min_confidence_floor = min_confidence_floor
        self.max_confidence_ceiling = max_confidence_ceiling
        self.confidence_step = confidence_step
        self.target_win_rate = target_win_rate
        self.last_tune_time = None
        self.last_result = None

    def _load_recent_trades(self):
        if not os.path.exists(self.db_path):
            return pd.DataFrame()
        conn = sqlite3.connect(self.db_path)
        df = pd.read_sql_query(
            """
            SELECT confidence, pnl, r_multiple, regime, timestamp
            FROM trades
            ORDER BY id DESC
            LIMIT ?
            """,
            conn,
            params=(int(self.lookback_trades),),
        )
        conn.close()
        return df

    def maybe_tune(self, current_min_confidence):
        now = datetime.utcnow()
        if self.last_tune_time is None:
            return self.tune(current_min_confidence)
        elapsed = (now - self.last_tune_time).total_seconds()
        if elapsed >= self.tune_interval_seconds:
            return self.tune(current_min_confidence)
        return {
            "status": "skipped",
            "reason": "interval_not_reached",
            "seconds_remaining": int(self.tune_interval_seconds - elapsed),
            "min_confidence": current_min_confidence,
            "last_result": self.last_result,
        }

    def tune(self, current_min_confidence):
        df = self._load_recent_trades()
        if df.empty or len(df) < self.min_samples:
            result = {
                "status": "not_enough_data",
                "samples": 0 if df.empty else int(len(df)),
                "min_required": int(self.min_samples),
                "min_confidence": current_min_confidence,
            }
            self.last_tune_time = datetime.utcnow()
            self.last_result = result
            return result

        if "r_multiple" not in df.columns:
            df["r_multiple"] = 0.0

        candidates = []
        for c in range(
            int(self.min_confidence_floor),
            int(self.max_confidence_ceiling) + 1,
            int(max(1, self.confidence_step)),
        ):
            sample = df[df["confidence"] >= c]
            n = len(sample)
            if n < max(10, self.min_samples // 3):
                continue
            wins = int((sample["pnl"] > 0).sum())
            win_rate = (wins / n) * 100.0
            expectancy = float(sample["r_multiple"].fillna(0.0).mean())
            avg_pnl = float(sample["pnl"].fillna(0.0).mean())

            score = (win_rate * 0.6) + (expectancy * 25.0) + (max(0.0, avg_pnl) / 1000.0)
            if win_rate >= self.target_win_rate:
                score += 3.0
            if expectancy > 0:
                score += 2.0

            candidates.append(
                {
                    "confidence": c,
                    "sample_size": int(n),
                    "win_rate": round(win_rate, 2),
                    "expectancy_r": round(expectancy, 3),
                    "avg_pnl": round(avg_pnl, 2),
                    "score": round(score, 3),
                }
            )

        if not candidates:
            result = {
                "status": "no_valid_candidate",
                "samples": int(len(df)),
                "min_confidence": current_min_confidence,
            }
            self.last_tune_time = datetime.utcnow()
            self.last_result = result
            return result

        best = max(candidates, key=lambda x: x["score"])
        tuned_conf = int(best["confidence"])
        
        # PERSIST: Store the tuned confidence in control_state.json so it survives restarts
        try:
            upsert_overrides({"DYNAMIC_MIN_CONFIDENCE": tuned_conf})
        except Exception:
            pass

        result = {
            "status": "tuned",
            "previous_min_confidence": float(current_min_confidence),
            "min_confidence": tuned_conf,
            "samples": int(len(df)),
            "selected": best,
            "top_candidates": sorted(candidates, key=lambda x: x["score"], reverse=True)[:5],
        }

        self.last_tune_time = datetime.utcnow()
        self.last_result = result
        return result
