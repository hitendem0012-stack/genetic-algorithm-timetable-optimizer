from pathlib import Path
import sqlite3

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / 'timetable.db'
SCHEMA_PATH = Path(__file__).with_name('schema.sql')


def connect():
    connection = sqlite3.connect(DB_PATH)
    connection.execute('PRAGMA foreign_keys = ON')
    return connection


def initialize_database():
    with connect() as connection:
        connection.executescript(SCHEMA_PATH.read_text(encoding='utf-8'))
        connection.executemany(
            'INSERT OR IGNORE INTO time_slots (slot_id, weekday, period_number) VALUES (?, ?, ?)',
            [(day * 6 + period, day, period) for day in range(5) for period in range(1, 7)],
        )
        count = connection.execute('SELECT COUNT(*) FROM time_slots').fetchone()[0]
    return count


if __name__ == '__main__':
    print(f'Database ready! Time slots: {initialize_database()}')
