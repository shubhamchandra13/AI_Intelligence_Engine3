import sqlite3
import os

db_path = r"C:\Users\Shubham Chandra\Desktop\AI_System_Engine\database\trades.db"

def check_counts():
    if not os.path.exists(db_path):
        print(f"❌ Database file not found at: {db_path}")
        return

    try:
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        
        # Check trades table
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='trades';")
        if cur.fetchone():
            cur.execute("SELECT COUNT(*) FROM trades")
            trades_count = cur.fetchone()[0]
            print(f"📊 Trades Count: {trades_count}")
        else:
            print("⚠️ 'trades' table does not exist yet.")

        # Check ai_feature_store table
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='ai_feature_store';")
        if cur.fetchone():
            cur.execute("SELECT COUNT(*) FROM ai_feature_store")
            features_count = cur.fetchone()[0]
            print(f"🧠 AI Features Count: {features_count}")
        else:
            print("⚠️ 'ai_feature_store' table does not exist yet.")

        conn.close()
    except Exception as e:
        print(f"❌ Error checking database: {e}")

if __name__ == "__main__":
    check_counts()
