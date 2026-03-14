import sqlite3
import pandas as pd

def check_trades():
    conn = sqlite3.connect('C:/Users/Shubham Chandra/Desktop/AI_Intelligence_engine2/database/trades.db')
    try:
        df = pd.read_sql_query("SELECT * FROM trades", conn)
        print(f"Total trades: {len(df)}")
        if not df.empty:
            print("\nLast 5 trades:")
            print(df.tail())
            print("\nSummary:")
            print(df[['pnl', 'r_multiple']].describe())
            print("\nExit Reasons:")
            print(df['exit_reason'].value_counts())
    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    check_trades()
