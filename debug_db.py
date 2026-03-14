
import sqlite3
import pandas as pd

def debug_db():
    db_path = r"C:\Users\Shubham Chandra\Desktop\AI_Intelligence_engine2\database\trades.db"
    conn = sqlite3.connect(db_path)
    df = pd.read_sql_query("SELECT * FROM trades", conn)
    conn.close()
    
    if df.empty:
        print("No trades in database.")
        return
        
    print(f"Total trades: {len(df)}")
    print(f"Columns: {df.columns.tolist()}")
    
    # Use available columns
    cols = [c for c in ['id', 'pnl', 'capital_before', 'capital_after'] if c in df.columns]
    print("\nLast 10 trades:")
    print(df[cols].tail(10))
    
    if 'capital_after' in df.columns:
        equity = df["capital_after"]
        peak = equity.cummax()
        drawdown = (equity - peak) / peak * 100
        print(f"\nCalculated Min Drawdown: {drawdown.min()}%")
        print(f"Max Equity Peak: {peak.max()}")
        print(f"Current Equity: {equity.iloc[-1]}")
        
        # Check for abnormal values
        print(f"Min capital_after: {equity.min()}")
        print(f"Max capital_after: {equity.max()}")

if __name__ == "__main__":
    debug_db()
