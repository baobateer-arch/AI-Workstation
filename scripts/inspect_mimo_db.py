"""Inspect MiMo SQLite database."""
import sqlite3
from pathlib import Path

db_path = Path.home() / ".local" / "share" / "mimocode" / "mimocode.db"
conn = sqlite3.connect(db_path)

# List all tables
tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
print("Tables:", [t[0] for t in tables])

for t in tables:
    name = t[0]
    schema = conn.execute(f"PRAGMA table_info({name})").fetchall()
    count = conn.execute(f"SELECT COUNT(*) FROM {name}").fetchone()[0]
    print(f"\nTable {name} ({count} rows):")
    for col in schema:
        print(f"  {col[1]} ({col[2]})")
    # Show last 2 rows
    try:
        rows = conn.execute(f"SELECT * FROM {name} ORDER BY rowid DESC LIMIT 2").fetchall()
        for r in rows:
            print(f"  -> {str(r)[:300]}")
    except Exception as e:
        print(f"  Error reading rows: {e}")

conn.close()
