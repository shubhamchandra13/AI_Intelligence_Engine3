import sqlite3
import pandas as pd
import json

class EvaluationEngine:
    """
    Computes performance metrics and evaluates trade outcomes.
    Differentiates between LIVE_PAPER and HISTORICAL_REPLAY.
    """
    def __init__(self, db_path="database/trades.db"):
        self.db_path = db_path

    def _get_trades_df(self, trade_mode=None, replay_batch_id=None):
        try:
            conn = sqlite3.connect(self.db_path)
            query = "SELECT * FROM trades"
            conditions = []
            params = []
            
            if trade_mode:
                conditions.append("trade_mode = ?")
                params.append(trade_mode)
            if replay_batch_id:
                conditions.append("replay_batch_id = ?")
                params.append(replay_batch_id)
                
            if conditions:
                query += " WHERE " + " AND ".join(conditions)
                
            df = pd.read_sql_query(query, conn, params=params)
            conn.close()
            return df
        except Exception as e:
            print(f"Failed to load trades: {e}")
            return pd.DataFrame()

    def evaluate_performance(self, trade_mode=None, replay_batch_id=None):
        df = self._get_trades_df(trade_mode, replay_batch_id)
        if df.empty:
            return {"status": "NO_DATA"}
            
        wins = df[df['pnl'] > 0]
        losses = df[df['pnl'] <= 0]
        
        total_trades = len(df)
        win_rate = (len(wins) / total_trades) * 100 if total_trades > 0 else 0
        
        avg_win = wins['pnl'].mean() if not wins.empty else 0
        avg_loss = abs(losses['pnl'].mean()) if not losses.empty else 0
        
        expectancy = (win_rate/100 * avg_win) - ((1 - win_rate/100) * avg_loss)
        profit_factor = wins['pnl'].sum() / abs(losses['pnl'].sum()) if abs(losses['pnl'].sum()) > 0 else float('inf')
        
        # Max Drawdown estimation (simplified cumulative PnL drawdown)
        cumulative_pnl = df['pnl'].cumsum()
        peak = cumulative_pnl.cummax()
        drawdown = peak - cumulative_pnl
        max_drawdown = drawdown.max()
        
        return {
            "status": "SUCCESS",
            "total_trades": total_trades,
            "win_rate": round(win_rate, 2),
            "expectancy": round(expectancy, 2),
            "profit_factor": round(profit_factor, 2),
            "max_drawdown": round(max_drawdown, 2),
            "net_pnl": round(df['pnl'].sum(), 2)
        }

    def evaluate_by_regime(self, trade_mode=None, replay_batch_id=None):
        df = self._get_trades_df(trade_mode, replay_batch_id)
        if df.empty or 'regime' not in df.columns:
            return {}
            
        grouped = df.groupby('regime')
        stats = {}
        for name, group in grouped:
            wins = group[group['pnl'] > 0]
            win_rate = len(wins) / len(group) * 100
            stats[name] = {
                "trades": len(group),
                "win_rate": round(win_rate, 2),
                "net_pnl": round(group['pnl'].sum(), 2)
            }
        return stats

    def evaluate_by_confidence(self, trade_mode=None, replay_batch_id=None):
        df = self._get_trades_df(trade_mode, replay_batch_id)
        if df.empty or 'confidence' not in df.columns:
            return {}
            
        # Create bins 0-10, 10-20, ...
        bins = range(0, 110, 10)
        labels = [f"{i}-{i+10}" for i in range(0, 100, 10)]
        df['conf_bin'] = pd.cut(df['confidence'], bins=bins, labels=labels, right=False)
        
        grouped = df.groupby('conf_bin')
        stats = {}
        for name, group in grouped:
            if len(group) == 0: continue
            wins = group[group['pnl'] > 0]
            win_rate = len(wins) / len(group) * 100
            stats[name] = {
                "trades": len(group),
                "win_rate": round(win_rate, 2),
                "net_pnl": round(group['pnl'].sum(), 2)
            }
        return stats
