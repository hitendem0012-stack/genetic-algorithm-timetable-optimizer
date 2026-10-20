
from database.db import connect


def save_timetable(result, generations_run=None, connection=None):
    """Save a valid timetable and all its weekly occurrences."""

    assignments = result.get("best_timetable")

    if assignments is None:
        raise ValueError("No timetable candidate was provided.")

    if not result.get("is_valid", False):
        raise ValueError(
            "Cannot save an invalid timetable. "
            "Resolve hard-constraint violations first."
        )

    if generations_run is None:
        generations_run = result.get("generations", 0)

    def insert_records(db):
        # Additive migration: safe for an existing database.
        db.execute("""
            CREATE TABLE IF NOT EXISTS timetable_occurrences (
                occurrence_id INTEGER PRIMARY KEY AUTOINCREMENT,
                timetable_id INTEGER NOT NULL
                    REFERENCES timetables(timetable_id) ON DELETE CASCADE,
                session_id INTEGER NOT NULL
                    REFERENCES class_sessions(session_id),
                occurrence_number INTEGER NOT NULL
                    CHECK(occurrence_number >= 1),
                start_slot_id INTEGER NOT NULL
                    REFERENCES time_slots(slot_id),
                room_id INTEGER NOT NULL REFERENCES rooms(room_id),
                UNIQUE(timetable_id, session_id, occurrence_number)
            )
        """)

        cursor = db.execute(
            """
            INSERT INTO timetables (fitness, penalty, generations_run)
            VALUES (?, ?, ?)
            """,
            (
                result["fitness"],
                result["hard_penalty"],
                generations_run,
            ),
        )

        timetable_id = cursor.lastrowid
        seen_sessions = set()
        occurrence_counts = {}

        for assignment in assignments:
            session_id = assignment["session_id"]
            gene_id = assignment.get("gene_id")

            if gene_id is None:
                occurrence_number = occurrence_counts.get(session_id, 0) + 1
            elif (
                isinstance(gene_id, tuple)
                and len(gene_id) == 2
                and gene_id[0] == session_id
                and isinstance(gene_id[1], int)
                and not isinstance(gene_id[1], bool)
                and gene_id[1] >= 1
            ):
                occurrence_number = gene_id[1]
            else:
                raise ValueError(
                    f"Invalid occurrence identity for session {session_id}."
                )

            occurrence_counts[session_id] = max(
                occurrence_counts.get(session_id, 0),
                occurrence_number,
            )

            db.execute(
                """
                INSERT INTO timetable_occurrences (
                    timetable_id, session_id, occurrence_number,
                    start_slot_id, room_id
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    timetable_id,
                    session_id,
                    occurrence_number,
                    assignment["start_slot"],
                    assignment["room_id"],
                ),
            )

            # Keep one legacy assignment per original session.
            if session_id not in seen_sessions:
                db.execute(
                    """
                    INSERT INTO timetable_assignments (
                        timetable_id, session_id, start_slot_id, room_id
                    )
                    VALUES (?, ?, ?, ?)
                    """,
                    (
                        timetable_id,
                        session_id,
                        assignment["start_slot"],
                        assignment["room_id"],
                    ),
                )
                seen_sessions.add(session_id)

        return timetable_id

    if connection is not None:
        return insert_records(connection)

    with connect() as db:
        return insert_records(db)
