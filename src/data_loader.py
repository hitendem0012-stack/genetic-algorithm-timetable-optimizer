
from database.db import connect


def load_problem_data():
    """Load teachers, subjects, groups, rooms, and sessions from SQLite."""

    with connect() as connection:
        connection.row_factory = __import__("sqlite3").Row

        teachers = [
            dict(row)
            for row in connection.execute(
                "SELECT teacher_id, name FROM teachers"
            ).fetchall()
        ]

        
        subjects = [
            dict(row)
            for row in connection.execute(
                """
                SELECT
                    subject_id,
                    COALESCE(NULLIF(subject_name, ''), name) AS name,
                    subject_code,
                    department,
                    subject_type,
                    requires_lab
                FROM subjects
                """
            ).fetchall()
        ]

        groups = [
            dict(row)
            for row in connection.execute(
                """
                SELECT
                    group_id,
                    COALESCE(NULLIF(group_name, ''), name) AS name,
                    department,
                    semester,
                    student_count
                FROM student_groups
                """
            ).fetchall()
        ]

        rooms = [
            dict(row)
            for row in connection.execute(
                """
                SELECT
                    room_id,
                    COALESCE(NULLIF(room_name, ''), name) AS name,
                    capacity,
                    room_type
                FROM rooms
                """
            ).fetchall()
        ]

        
        sessions = [
            dict(row)
            for row in connection.execute(
                """
                SELECT
                    cs.session_id,
                    cs.subject_id,
                    cs.teacher_id,
                    cs.group_id,
                    cs.duration_periods,
                    cs.sessions_per_week,
                    s.name AS subject_name,
                    s.room_type_required,
                    g.student_count
                FROM class_sessions AS cs
                JOIN subjects AS s
                    ON s.subject_id = cs.subject_id
                JOIN student_groups AS g
                    ON g.group_id = cs.group_id
                ORDER BY cs.session_id
                """
            ).fetchall()
        ]

        slots = [
            dict(row)
            for row in connection.execute(
                """
                SELECT slot_id, weekday, period_number
                FROM time_slots
                ORDER BY slot_id
                """
            ).fetchall()
        ]

        
        unavailability = [
            dict(row)
            for row in connection.execute(
                """
                SELECT resource_type, resource_id, slot_id
                FROM resource_unavailability
                """
            ).fetchall()
        ]


    # Adapt database records to the current algorithm's input format.
    for session in sessions:
        required_type = (
            session["room_type_required"] or "classroom"
        ).strip().lower()

        session["requires_lab"] = "lab" in required_type

    return {
        "teachers": teachers,
        "subjects": subjects,
        "groups": groups,
        "rooms": rooms,
        "sessions": sessions,
        "time_slots": slots,
        "resource_unavailability": unavailability,
    }
