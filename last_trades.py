import sqlite3
import os

db_path = r"C:\Users\Shubham Chandra\Desktop\AI_Intelligence_Engine\database\trades.db"

def last_trades():
    if not os.path.exists(db_path):
        print(f"❌ Database file not found at: {db_path}")
        return

    try:
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        
        cur.execute("PRAGMA table_info(trades)")
        cols = [c[1] for c in cur.fetchall()]
        
        cur.execute("SELECT * FROM trades ORDER BY id DESC LIMIT 5")
        rows = cur.fetchall()
        for r in rows:
            trade_dict = dict(zip(cols, r))
            print(f"ID: {trade_dict.get('id')} | {trade_dict.get('index_name')} | {trade_dict.get('direction')} | PnL: {trade_dict.get('pnl')} | Time: {trade_dict.get('timestamp')}")

        conn.close()
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    last_trades()
