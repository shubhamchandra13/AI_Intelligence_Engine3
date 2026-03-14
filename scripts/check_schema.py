import sqlite3
import os

db_path = os.path.join("database", "trades.db")
conn = sqlite3.connect(db_path)
cur = conn.cursor()

# Get tables
cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cur.fetchall()
print("Tables:", tables)

for table in tables:
    table_name = table[0]
    print(f"\nSchema for {table_name}:")
    cur.execute(f"SELECT sql FROM sqlite_master WHERE type='table' AND name='{table_name}';")
    print(cur.fetchone()[0])

conn.close()
