import sqlite3
import pandas as pd
import os
import json
from datetime import datetime

class MetaLearningEngine:
    """
    AI Meta-Learning Layer: Analyzes past performance to judge current setups.
    It acts as an internal 'Judge' to refine confidence scores.
    """
    def __init__(self, db_path="database/trades.db"):
        self.db_path = db_path
        self.performance_cache = {}

    def refresh_knowledge(self):
        """Reloads historical trade data and identifies winning patterns."""
        if not os.path.exists(self.db_path):
            return

        try:
            conn = sqlite3.connect(self.db_path)
            # Fetch features and outcomes
            query = """
                SELECT regime, confidence, pnl, exit_reason, r_multiple 
                FROM trades 
                WHERE pnl IS NOT NULL
            """
            df = pd.read_sql_query(query, conn)
            conn.close()

            if len(df) < 5:
                return

            # Analyze win rates by regime and confidence buckets
            df['is_win'] = df['pnl'] > 0
            regime_stats = df.groupby('regime')['is_win'].mean().to_dict()
            
            self.performance_cache = {
                "regime_win_rates": regime_stats,
                "avg_r_multiple": df['r_multiple'].mean(),
                "total_samples": len(df)
            }
        except Exception as e:
            print(f"Meta-Learning Refresh Error: {e}")

    def judge_setup(self, current_regime, current_confidence):
        """
        Provides a Meta-Score (0.5 to 1.5) based on historical edge.
        1.0 = Neutral, >1.0 = High Edge, <1.0 = Low Edge.
        """
        if not self.performance_cache:
            return 1.0, "No historical data yet."

        regime_win_rate = self.performance_cache.get("regime_win_rates", {}).get(current_regime, 0.5)
        
        # Meta Adjustment Logic
        adjustment = 1.0
        reason = "Neutral historical edge."

        if regime_win_rate > 0.6:
            adjustment = 1.2
            reason = f"Strong historical edge in {current_regime} ({round(regime_win_rate*100)}% Win Rate)."
        elif regime_win_rate < 0.4:
            adjustment = 0.8
            reason = f"Weak historical edge in {current_regime} ({round(regime_win_rate*100)}% Win Rate)."

        # Confidence sanity check
        if current_confidence > 80 and regime_win_rate < 0.45:
            adjustment *= 0.9
            reason += " | High confidence mismatch with historical win rate."

        return round(adjustment, 2), reason
