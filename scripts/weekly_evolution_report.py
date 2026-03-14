import sqlite3
import sys
from pathlib import Path
from datetime import datetime, timedelta

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engines.ml_evolution_engine import MLEvolutionEngine


DB_PATH = "database/trades.db"


def load_recent_trades(days=7):
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM trades ORDER BY timestamp ASC", conn)
    conn.close()
    if df.empty:
        return df

    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    cutoff = datetime.utcnow() - timedelta(days=days)
    df = df[df["timestamp"] >= cutoff].copy()
    return df


def summarize(df):
    if df.empty:
        return {"status": "no_data"}

    df["is_profit"] = (df["pnl"] > 0).astype(int)
    total = len(df)
    win_rate = round(df["is_profit"].mean() * 100, 2)
    avg_pnl = round(df["pnl"].mean(), 2)
    expectancy_r = round(df["r_multiple"].fillna(0).mean(), 3)

    group_cols = ["regime", "iv_regime"]
    if "confidence" in df.columns:
        bins = [0, 30, 40, 50, 60, 70, 80, 101]
        labels = ["<30", "30-40", "40-50", "50-60", "60-70", "70-80", "80+"]
        df["conf_bucket"] = pd.cut(df["confidence"], bins=bins, labels=labels, include_lowest=True)
        group_cols.append("conf_bucket")

    combo = (
        df.groupby(group_cols, dropna=False, observed=False)
        .agg(
            trades=("id", "count"),
            win_rate=("is_profit", "mean"),
            avg_pnl=("pnl", "mean"),
            expectancy_r=("r_multiple", "mean"),
        )
        .reset_index()
    )
    combo["win_rate"] = (combo["win_rate"] * 100).round(2)
    combo["avg_pnl"] = combo["avg_pnl"].round(2)
    combo["expectancy_r"] = combo["expectancy_r"].fillna(0).round(3)

    min_group = 3
    reliable = combo[combo["trades"] >= min_group].copy()
    if reliable.empty:
        reliable = combo.copy()

    best = reliable.sort_values(["expectancy_r", "win_rate"], ascending=[False, False]).head(5)
    worst = reliable.sort_values(["expectancy_r", "win_rate"], ascending=[True, True]).head(5)

    return {
        "status": "ok",
        "total_trades": int(total),
        "win_rate": win_rate,
        "avg_pnl": avg_pnl,
        "expectancy_r": expectancy_r,
        "best_combos": best.to_dict("records"),
        "worst_combos": worst.to_dict("records"),
    }


def main():
    print("=" * 80)
    print("WEEKLY EVOLUTION REPORT")
    print("=" * 80)

    df = load_recent_trades(days=7)
    summary = summarize(df)

    if summary["status"] == "no_data":
        print("No trades found in the last 7 days.")
        return

    print(f"Trades: {summary['total_trades']}")
    print(f"Win Rate: {summary['win_rate']}%")
    print(f"Avg PnL: {summary['avg_pnl']}")
    print(f"Expectancy (R): {summary['expectancy_r']}")

    print("\nTop 5 Performing Combos")
    for row in summary["best_combos"]:
        print(row)

    print("\nBottom 5 Performing Combos")
    for row in summary["worst_combos"]:
        print(row)

    ml = MLEvolutionEngine()
    retrain_status = ml.retrain()
    print("\nModel Retrain")
    print(retrain_status)

    if retrain_status.get("status") == "trained":
        meta_preview = ml.predict_meta_label({
            "confidence": 55,
            "risk_percent": 1,
            "risk_used": 1,
            "target_used": 2,
            "trade_duration": 30,
            "regime": "RANGE_NORMAL_VOL",
            "iv_regime": "NORMAL_IV",
            "index_name": "BANKNIFTY",
            "direction": "Bullish",
            "hour": 11,
            "weekday": 2,
        })
        print("\nMeta-label Preview")
        print(meta_preview)

    print("=" * 80)


if __name__ == "__main__":
    main()
