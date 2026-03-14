
import sqlite3
import json

def inspect_today_system():
    db_path = r"C:\Users\Shubham Chandra\Desktop\AI_Intelligence_Engine\database\trades.db"
    today = "2026-03-13"
    print(f"Checking DB: {db_path} for date: {today}")
    try:
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        # First get column names
        cur.execute("PRAGMA table_info(trades)")
        cols = [c[1] for c in cur.fetchall()]
        
        cur.execute("SELECT * FROM trades WHERE timestamp LIKE ? ORDER BY id ASC", (f"{today}%",))
        rows = cur.fetchall()
        print(f"Total trades today in AI_Intelligence_Engine: {len(rows)}")
        for r in rows:
            trade_dict = dict(zip(cols, r))
            # Just print the important stuff
            print(f"ID: {trade_dict.get('id')} | {trade_dict.get('index_name')} | {trade_dict.get('direction')} | Entry: {trade_dict.get('entry_price')} | Exit: {trade_dict.get('exit_price')} | PnL: {trade_dict.get('pnl')} | Reason: {trade_dict.get('exit_reason')} | Time: {trade_dict.get('timestamp')}")
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    inspect_today_system()
