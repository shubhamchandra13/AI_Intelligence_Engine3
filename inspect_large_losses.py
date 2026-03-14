import sqlite3
import pandas as pd

def find_large_losses():
    conn = sqlite3.connect('C:/Users/Shubham Chandra/Desktop/AI_Intelligence_engine2/database/trades.db')
    try:
        df = pd.read_sql_query("SELECT * FROM trades WHERE pnl < -3000", conn)
        print(f"Large loss trades: {len(df)}")
        if not df.empty:
            print(df[['id', 'index_name', 'pnl', 'entry_price', 'exit_price', 'exit_reason', 'r_multiple']])
    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    find_large_losses()
