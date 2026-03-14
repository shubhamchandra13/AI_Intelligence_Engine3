# ============================================================
# 📈 EQUITY CURVE RISK SCALING ENGINE (THE FUND MANAGER)
# Level 5 Ultimate Autonomy Upgrade
# Monitors Win Streaks & Drawdowns to Scale Risk Dynamically
# ============================================================

import sqlite3
import pandas as pd

class EquityCurveEngine:
    def __init__(self, db_path="database/trades.db"):
        self.db_path = db_path

    def get_equity_risk_multiplier(self, lookback_trades=10):
        """
        Analyzes the equity curve and returns a risk multiplier.
        - Win Streak (Last 3 days or X trades profitable): Scale Up (Aggressive)
        - Drawdown (Last X trades in loss): Scale Down (Conservative)
        """
        try:
            conn = sqlite3.connect(self.db_path)
            # We need pnl and timestamp to see the trend
            df = pd.read_sql_query(
                f"SELECT pnl, timestamp FROM trades ORDER BY id DESC LIMIT {lookback_trades}", 
                conn
            )
            conn.close()

            if df.empty or len(df) < 3:
                return 1.0 # Neutral multiplier for new systems

            # Reverse to get chronological order for streak analysis
            df = df.iloc[::-1].reset_index(drop=True)
            
            pnls = df['pnl'].tolist()
            last_3 = pnls[-3:] if len(pnls) >= 3 else pnls
            
            # --- WIN STREAK LOGIC (Aggressive) ---
            # If last 3 trades are all wins
            if len(last_3) == 3 and all(x > 0 for x in last_3):
                return 1.5 # 50% increase in risk
            
            # If 4 out of last 5 trades are wins
            if len(pnls) >= 5:
                last_5 = pnls[-5:]
                wins_in_5 = sum(1 for x in last_5 if x > 0)
                if wins_in_5 >= 4:
                    return 1.3 # 30% increase
            
            # --- DRAWDOWN LOGIC (Conservative) ---
            # If last 3 trades are all losses
            if len(last_3) == 3 and all(x <= 0 for x in last_3):
                return 0.5 # 50% decrease in risk
                
            # If 4 out of last 5 trades are losses
            if len(pnls) >= 5:
                last_5 = pnls[-5:]
                losses_in_5 = sum(1 for x in last_5 if x <= 0)
                if losses_in_5 >= 4:
                    return 0.6 # 40% decrease
            
            # --- EQUITY CURVE TREND (Moving Average of PnL) ---
            avg_pnl = sum(pnls) / len(pnls)
            if avg_pnl > 0:
                return 1.1 # Slight boost for positive expectancy
            elif avg_pnl < 0:
                return 0.8 # Slight reduction for negative expectancy

            return 1.0

        except Exception as e:
            print(f"⚠️ EquityCurveEngine Error: {e}")
            return 1.0
