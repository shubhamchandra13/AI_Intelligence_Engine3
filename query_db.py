import sqlite3
import os

db_path = r"C:\Users\Shubham Chandra\Desktop\AI_Intelligence_Engine\database\trades.db"

def query_db():
    if not os.path.exists(db_path):
        print(f"❌ Database file not found at: {db_path}")
        return

    try:
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        
        cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cur.fetchall()
        print(f"Tables: {[t[0] for t in tables]}")
        
        for table in tables:
            t_name = table[0]
            cur.execute(f"SELECT COUNT(*) FROM {t_name}")
            count = cur.fetchone()[0]
            print(f"Table {t_name}: {count} rows")

        conn.close()
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    query_db()
