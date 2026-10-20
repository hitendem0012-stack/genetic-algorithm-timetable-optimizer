
import sqlite3

conn = sqlite3.connect("timetable.db")

tables = conn.execute(
    "SELECT name FROM sqlite_master WHERE type='table'"
).fetchall()

print("DATABASE TABLES:")

for (table_name,) in tables:
    print(f"\n{table_name}:")
    columns = conn.execute(
        f"PRAGMA table_info({table_name})"
    ).fetchall()

    for column in columns:
        print(" -", column[1])

conn.close()
