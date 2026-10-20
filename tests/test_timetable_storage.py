
import sys
from pathlib import Path
import sqlite3

sys.path.insert(
    0,
    str(Path(__file__).resolve().parents[1])
)

from src.timetable_storage import save_timetable


def test_invalid_timetable_is_not_saved():
    import pytest

    result = {
        "best_timetable": [
            {"session_id": 1, "start_slot": 1, "room_id": 1}
        ],
        "fitness": 1 / 101,
        "hard_penalty": 100,
        "is_valid": False,
        "violations": ["Test violation"],
        "generations": 2,
    }

    with pytest.raises(ValueError):
        save_timetable(result)


def test_missing_timetable_is_not_saved():
    import pytest

    with pytest.raises(ValueError):
        save_timetable({"best_timetable": None})


def test_valid_timetable_is_saved_to_temporary_database(tmp_path):
    db_path = tmp_path / "test_timetable.db"

    connection = sqlite3.connect(db_path)
    connection.execute("PRAGMA foreign_keys = ON")

    connection.executescript("""
        CREATE TABLE class_sessions (
            session_id INTEGER PRIMARY KEY
        );

        CREATE TABLE time_slots (
            slot_id INTEGER PRIMARY KEY
        );

        CREATE TABLE rooms (
            room_id INTEGER PRIMARY KEY
        );

        CREATE TABLE timetables (
            timetable_id INTEGER PRIMARY KEY,
            fitness REAL NOT NULL,
            penalty REAL NOT NULL,
            generations_run INTEGER NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE timetable_assignments (
            timetable_id INTEGER NOT NULL
                REFERENCES timetables(timetable_id) ON DELETE CASCADE,
            session_id INTEGER NOT NULL
                REFERENCES class_sessions(session_id),
            start_slot_id INTEGER NOT NULL
                REFERENCES time_slots(slot_id),
            room_id INTEGER NOT NULL
                REFERENCES rooms(room_id),
            PRIMARY KEY (timetable_id, session_id)
        );

        INSERT INTO class_sessions VALUES (1);
        INSERT INTO time_slots VALUES (1);
        INSERT INTO rooms VALUES (1);
    """)

    result = {
        "best_timetable": [
            {"session_id": 1, "start_slot": 1, "room_id": 1}
        ],
        "fitness": 1.0,
        "hard_penalty": 0,
        "is_valid": True,
        "violations": [],
        "generations": 5,
    }

    try:
        timetable_id = save_timetable(result, connection=connection)

        saved = connection.execute(
            """
            SELECT fitness, penalty, generations_run
            FROM timetables
            WHERE timetable_id = ?
            """,
            (timetable_id,),
        ).fetchone()

        assignment = connection.execute(
            """
            SELECT session_id, start_slot_id, room_id
            FROM timetable_assignments
            WHERE timetable_id = ?
            """,
            (timetable_id,),
        ).fetchone()

        assert saved == (1.0, 0, 5)
        assert assignment == (1, 1, 1)

    finally:
        connection.close()


def test_repeated_occurrences_are_saved_safely(tmp_path):
    db_path = tmp_path / "test_repeated_occurrences.db"

    connection = sqlite3.connect(db_path)
    connection.execute("PRAGMA foreign_keys = ON")

    connection.executescript("""
        CREATE TABLE class_sessions (
            session_id INTEGER PRIMARY KEY
        );

        CREATE TABLE time_slots (
            slot_id INTEGER PRIMARY KEY
        );

        CREATE TABLE rooms (
            room_id INTEGER PRIMARY KEY
        );

        CREATE TABLE timetables (
            timetable_id INTEGER PRIMARY KEY,
            fitness REAL NOT NULL,
            penalty REAL NOT NULL,
            generations_run INTEGER NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE timetable_assignments (
            timetable_id INTEGER NOT NULL
                REFERENCES timetables(timetable_id) ON DELETE CASCADE,
            session_id INTEGER NOT NULL
                REFERENCES class_sessions(session_id),
            start_slot_id INTEGER NOT NULL
                REFERENCES time_slots(slot_id),
            room_id INTEGER NOT NULL
                REFERENCES rooms(room_id),
            PRIMARY KEY (timetable_id, session_id)
        );

        INSERT INTO class_sessions VALUES (1);
        INSERT INTO time_slots VALUES (1), (2), (3);
        INSERT INTO rooms VALUES (1);
    """)

    result = {
        "best_timetable": [
            {
                "session_id": 1,
                "gene_id": (1, 1),
                "start_slot": 1,
                "room_id": 1,
            },
            {
                "session_id": 1,
                "gene_id": (1, 2),
                "start_slot": 2,
                "room_id": 1,
            },
            {
                "session_id": 1,
                "gene_id": (1, 3),
                "start_slot": 3,
                "room_id": 1,
            },
        ],
        "fitness": 1.0,
        "hard_penalty": 0,
        "is_valid": True,
        "violations": [],
        "generations": 5,
    }

    try:
        timetable_id = save_timetable(result, connection=connection)

        occurrences = connection.execute(
            """
            SELECT occurrence_number, start_slot_id, room_id
            FROM timetable_occurrences
            WHERE timetable_id = ?
            ORDER BY occurrence_number
            """,
            (timetable_id,),
        ).fetchall()

        legacy_assignments = connection.execute(
            """
            SELECT session_id, start_slot_id, room_id
            FROM timetable_assignments
            WHERE timetable_id = ?
            """,
            (timetable_id,),
        ).fetchall()

        assert occurrences == [
            (1, 1, 1),
            (2, 2, 1),
            (3, 3, 1),
        ]

        # The legacy table keeps one row per original session.
        assert len(legacy_assignments) == 1
        assert legacy_assignments[0][0] == 1

    finally:
        connection.close()
