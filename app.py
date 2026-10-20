
import streamlit as st
import sqlite3
from pathlib import Path
from src.data_loader import load_problem_data
from src.genetic_algorithm import run_genetic_algorithm
from src.timetable_storage import save_timetable
from database.db import initialize_database

st.set_page_config(
    page_title="University Timetable Optimizer",
    page_icon="📅",
    layout="wide"
)

DB_PATH = Path(__file__).resolve().parent / "timetable.db"


def get_connection():
    return sqlite3.connect(DB_PATH)


def setup_tables():
    with get_connection() as conn:
        # Teachers table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS teachers (
                teacher_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                department TEXT NOT NULL DEFAULT '',
                email TEXT
            )
        """)

        teacher_columns = {
            row[1] for row in
            conn.execute("PRAGMA table_info(teachers)")
        }

        if "department" not in teacher_columns:
            conn.execute("""
                ALTER TABLE teachers
                ADD COLUMN department TEXT NOT NULL DEFAULT ''
            """)

        if "email" not in teacher_columns:
            conn.execute("""
                ALTER TABLE teachers ADD COLUMN email TEXT
            """)

        
        # Subjects table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS subjects (
                subject_id INTEGER PRIMARY KEY AUTOINCREMENT,
                subject_name TEXT NOT NULL DEFAULT '',
                subject_code TEXT NOT NULL DEFAULT '',
                department TEXT NOT NULL DEFAULT '',
                subject_type TEXT NOT NULL DEFAULT 'Theory',
                requires_lab INTEGER NOT NULL DEFAULT 0
            )
        """)

        # Migrate an existing subjects table safely
        subject_columns = {
            row[1] for row in conn.execute("PRAGMA table_info(subjects)")
        }

        required_columns = {
            "subject_name": "TEXT NOT NULL DEFAULT ''",
            "subject_code": "TEXT NOT NULL DEFAULT ''",
            "department": "TEXT NOT NULL DEFAULT ''",
            "subject_type": "TEXT NOT NULL DEFAULT 'Theory'",
            "requires_lab": "INTEGER NOT NULL DEFAULT 0"
        }

        for column, definition in required_columns.items():
            if column not in subject_columns:
                conn.execute(
                    f"ALTER TABLE subjects ADD COLUMN {column} {definition}"
                )

        # Preserve data if the old table used different column names
        subject_columns = {
            row[1] for row in conn.execute("PRAGMA table_info(subjects)")
        }

        if "name" in subject_columns:
            conn.execute("""
                UPDATE subjects
                SET subject_name = name
                WHERE subject_name = ''
            """)

        if "code" in subject_columns:
            conn.execute("""
                UPDATE subjects
                SET subject_code = code
                WHERE subject_code = ''
            """)
        
        
        # Student Groups table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS student_groups (
                group_id INTEGER PRIMARY KEY AUTOINCREMENT,
                group_name TEXT NOT NULL DEFAULT '',
                department TEXT NOT NULL DEFAULT '',
                semester INTEGER NOT NULL DEFAULT 1,
                student_count INTEGER NOT NULL DEFAULT 60
            )
        """)

        group_columns = {
            row[1]
            for row in conn.execute("PRAGMA table_info(student_groups)")
        }

        group_migrations = {
            "group_name": "TEXT NOT NULL DEFAULT ''",
            "department": "TEXT NOT NULL DEFAULT ''",
            "semester": "INTEGER NOT NULL DEFAULT 1",
            "student_count": "INTEGER NOT NULL DEFAULT 60"
        }

        for column, definition in group_migrations.items():
            if column not in group_columns:
                conn.execute(
                    f"ALTER TABLE student_groups ADD COLUMN {column} {definition}"
                )

        # Copy data from older column names if present
        group_columns = {
            row[1]
            for row in conn.execute("PRAGMA table_info(student_groups)")
        }

        if "name" in group_columns:
            conn.execute("""
                UPDATE student_groups
                SET group_name = name
                WHERE group_name = ''
            """)

        
        
        # Rooms and Labs table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS rooms (
                room_id INTEGER PRIMARY KEY AUTOINCREMENT,
                room_name TEXT NOT NULL DEFAULT '',
                room_type TEXT NOT NULL DEFAULT 'Classroom',
                capacity INTEGER NOT NULL DEFAULT 60
            )
        """)

        room_columns = {
            row[1]
            for row in conn.execute("PRAGMA table_info(rooms)")
        }

        room_migrations = {
            "room_name": "TEXT NOT NULL DEFAULT ''",
            "room_type": "TEXT NOT NULL DEFAULT 'Classroom'",
            "capacity": "INTEGER NOT NULL DEFAULT 60"
        }

        for column, definition in room_migrations.items():
            if column not in room_columns:
                conn.execute(
                    f"ALTER TABLE rooms ADD COLUMN {column} {definition}"
                )

        # Preserve names from an older schema
        room_columns = {
            row[1]
            for row in conn.execute("PRAGMA table_info(rooms)")
        }

        if "name" in room_columns:
            conn.execute("""
                UPDATE rooms
                SET room_name = name
                WHERE room_name = ''
            """)
        
        # Add sessions_per_week to an existing class_sessions table
        session_columns = {
            row[1]
            for row in conn.execute("PRAGMA table_info(class_sessions)")
        }

        if "sessions_per_week" not in session_columns:
            conn.execute("""
                ALTER TABLE class_sessions
                ADD COLUMN sessions_per_week INTEGER NOT NULL DEFAULT 1
            """)
initialize_database()
setup_tables()

st.title("📅 University Timetable Optimization System")
st.caption("Genetic Algorithm Based University Timetable Optimization System")

page = st.sidebar.radio(
    "Choose a section",
    ["Dashboard", "Teachers", "Subjects", "Student Groups", "Rooms & Labs", "Class Sessions", "Timetable Generation", "Saved Timetables"]
)

if page == "Dashboard":
    st.subheader("Project Dashboard")

    with get_connection() as conn:
        teacher_count = conn.execute(
            "SELECT COUNT(*) FROM teachers"
        ).fetchone()[0]

        subject_count = conn.execute(
            "SELECT COUNT(*) FROM subjects"
        ).fetchone()[0]

    col1, col2, col3 = st.columns(3)
    col1.metric("Working Days", "5")
    col2.metric("Periods per Day", "6")
    col3.metric("Weekly Time Slots", "30")

    col1, col2 = st.columns(2)
    col1.metric("Registered Teachers", teacher_count)
    col2.metric("Registered Subjects", subject_count)

    st.info("Add teachers and subjects before configuring class sessions.")

elif page == "Teachers":
    st.subheader("👨‍🏫 Teacher Management")
    st.write("Add and manage university teachers.")

    with st.form("teacher_form", clear_on_submit=True):
        name = st.text_input("Teacher Name *")
        department = st.text_input("Department *")
        email = st.text_input("Email (optional)")

        submitted = st.form_submit_button("➕ Add Teacher")

        if submitted:
            if not name.strip() or not department.strip():
                st.error("Teacher name and department are required.")
            else:
                with get_connection() as conn:
                    conn.execute(
                        """
                        INSERT INTO teachers (name, department, email)
                        VALUES (?, ?, ?)
                        """,
                        (name.strip(), department.strip(),
                         email.strip() or None)
                    )
                st.success(f"Teacher '{name.strip()}' added!")
                st.rerun()

    st.divider()
    st.subheader("📋 Registered Teachers")

    with get_connection() as conn:
        teachers = conn.execute(
            """
            SELECT teacher_id, name, department, email
            FROM teachers ORDER BY name
            """
        ).fetchall()

    if not teachers:
        st.info("No teachers added yet.")
    else:
        for tid, name, dept, email in teachers:
            with st.container(border=True):
                col1, col2 = st.columns([4, 1])
                with col1:
                    st.write(f"**{name}**")
                    st.caption(f"Department: {dept}")
                    st.caption(f"Email: {email or 'Not provided'}")
                with col2:
                    if st.button("🗑️ Delete", key=f"del_teacher_{tid}"):
                        with get_connection() as conn:
                            conn.execute(
                                "DELETE FROM teachers WHERE teacher_id = ?",
                                (tid,)
                            )
                        st.rerun()

elif page == "Subjects":
    st.subheader("📚 Subject Management")
    st.write("Add and manage subjects for the timetable.")

    with st.form("subject_form", clear_on_submit=True):
        subject_name = st.text_input("Subject Name *")
        subject_code = st.text_input("Subject Code *")
        department = st.text_input("Department *")

        subject_type = st.selectbox(
            "Subject Type",
            ["Theory", "Practical", "Lab"]
        )

        requires_lab = st.checkbox(
            "This subject requires a specialized lab"
        )

        submitted = st.form_submit_button("➕ Add Subject")

        if submitted:
            if not subject_name.strip():
                st.error("Subject name is required.")
            elif not subject_code.strip():
                st.error("Subject code is required.")
            elif not department.strip():
                st.error("Department is required.")
            else:
                try:
                    with get_connection() as conn:
                        conn.execute(
                            """
                            INSERT INTO subjects
                            (name, subject_name, subject_code, department,
                            subject_type, requires_lab)
                            VALUES (?, ?, ?, ?, ?, ?)
                            """,
                            (
                                subject_name.strip(),
                                subject_name.strip(),
                                subject_code.strip().upper(),
                                department.strip(),
                                subject_type,
                                int(requires_lab)
                            )
                        )
                    st.success(
                        f"Subject '{subject_name.strip()}' added successfully!"
                    )
                    st.rerun()
                except sqlite3.IntegrityError as e:
                    st.error(f"Database constraint error: {e}")

    st.divider()
    st.subheader("📋 Registered Subjects")

    with get_connection() as conn:
        subjects = conn.execute(
            """
            SELECT subject_id, subject_name, subject_code,
                   department, subject_type, requires_lab
            FROM subjects ORDER BY subject_name
            """
        ).fetchall()

    if not subjects:
        st.info("No subjects added yet. Use the form above.")
    else:
        for sid, name, code, dept, kind, lab in subjects:
            with st.container(border=True):
                col1, col2 = st.columns([4, 1])

                with col1:
                    st.write(f"**{name} ({code})**")
                    st.caption(f"Department: {dept}")
                    st.caption(f"Type: {kind}")
                    st.caption(
                        f"Specialized lab required: {'Yes' if lab else 'No'}"
                    )

                with col2:
                    if st.button("🗑️ Delete", key=f"del_subject_{sid}"):
                        with get_connection() as conn:
                            conn.execute(
                                "DELETE FROM subjects WHERE subject_id = ?",
                                (sid,)
                            )
                        st.rerun()

elif page == "Student Groups":
    st.subheader("👨‍🎓 Student Groups Management")
    st.write("Add and manage university classes and sections.")

    with st.form("student_group_form", clear_on_submit=True):
        group_name = st.text_input(
            "Group Name *",
            placeholder="e.g. BTech IT - Section A"
        )

        department = st.text_input(
            "Department *",
            placeholder="e.g. Information Technology"
        )

        semester = st.selectbox(
            "Semester *",
            options=list(range(1, 9))
        )

        student_count = st.number_input(
            "Number of Students *",
            min_value=1,
            max_value=500,
            value=60,
            step=1
        )

        submitted = st.form_submit_button("➕ Add Student Group")

        if submitted:
            if not group_name.strip() or not department.strip():
                st.error("Group name and department are required.")
            else:
                try:
                    with get_connection() as conn:
                        conn.execute(
                            """
                            INSERT INTO student_groups
                            (name, group_name, department, semester, student_count)
                            VALUES (?, ?, ?, ?, ?)
                            """,
                            (
                                group_name.strip(),
                                group_name.strip(),
                                department.strip(),
                                semester,
                                student_count
                            )
                        )

                    st.success(
                        f"Student group '{group_name.strip()}' added!"
                    )
                    st.rerun()

                except sqlite3.IntegrityError:
                    st.error(
                        "This group name already exists. Use a unique name."
                    )

    st.divider()
    st.subheader("📋 Registered Student Groups")

    with get_connection() as conn:
        groups = conn.execute(
            """
            SELECT group_id, group_name, department,
                   semester, student_count
            FROM student_groups
            ORDER BY group_name
            """
        ).fetchall()

    if not groups:
        st.info("No student groups added yet.")
    else:
        for gid, name, dept, sem, count in groups:
            with st.container(border=True):
                col1, col2 = st.columns([4, 1])

                with col1:
                    st.write(f"**{name}**")
                    st.caption(f"Department: {dept}")
                    st.caption(f"Semester: {sem}")
                    st.caption(f"Students: {count}")

                with col2:
                    if st.button(
                        "🗑️ Delete",
                        key=f"del_group_{gid}"
                    ):
                        with get_connection() as conn:
                            conn.execute(
                                "DELETE FROM student_groups WHERE group_id = ?",
                                (gid,)
                            )
                        st.rerun()

elif page == "Rooms & Labs":
    st.subheader("🏫 Rooms & Labs Management")
    st.write("Add and manage classrooms and specialized laboratories.")

    with st.form("room_form", clear_on_submit=True):
        room_name = st.text_input(
            "Room Name / Number *",
            placeholder="e.g. C-101 or Computer Lab 1"
        )

        room_type = st.selectbox(
            "Room Type *",
            [
                "Classroom",
                "Computer Lab",
                "Electronics Lab",
                "Physics Lab",
                "Chemistry Lab",
                "Other Lab"
            ]
        )

        capacity = st.number_input(
            "Room Capacity *",
            min_value=1,
            max_value=500,
            value=60,
            step=1
        )

        submitted = st.form_submit_button("➕ Add Room")

        if submitted:
            if not room_name.strip():
                st.error("Room name is required.")
            else:
                try:
                    with get_connection() as conn:
                        conn.execute(
                            """
                            INSERT INTO rooms
                            (name, room_name, room_type, capacity)
                            VALUES (?, ?, ?, ?)
                            """,
                            (
                                room_name.strip(),
                                room_name.strip(),
                                room_type,
                                capacity
                            )
                        )

                    st.success(f"Room '{room_name.strip()}' added successfully!")
                    st.rerun()

                except sqlite3.IntegrityError as e:
                    st.error(f"Could not add room: {e}")

    st.divider()
    st.subheader("📋 Registered Rooms & Labs")

    with get_connection() as conn:
        rooms = conn.execute(
            """
            SELECT room_id, room_name, room_type, capacity
            FROM rooms
            ORDER BY room_name
            """
        ).fetchall()

    if not rooms:
        st.info("No rooms added yet. Use the form above.")
    else:
        for rid, name, kind, capacity in rooms:
            with st.container(border=True):
                col1, col2 = st.columns([4, 1])

                with col1:
                    st.write(f"**{name}**")
                    st.caption(f"Room Type: {kind}")
                    st.caption(f"Capacity: {capacity} students")

                with col2:
                    if st.button("🗑️ Delete", key=f"del_room_{rid}"):
                        with get_connection() as conn:
                            conn.execute(
                                "DELETE FROM rooms WHERE room_id = ?",
                                (rid,)
                            )
                        st.rerun()

elif page == "Class Sessions":
    st.subheader("🧬 Class Sessions Management")
    st.write("Connect subjects, teachers and student groups.")

    with get_connection() as conn:
        teachers = conn.execute("""
            SELECT teacher_id, name
            FROM teachers
            ORDER BY name
        """).fetchall()

        subjects = conn.execute("""
            SELECT subject_id,
                   COALESCE(NULLIF(subject_name, ''), name)
            FROM subjects
            ORDER BY 2
        """).fetchall()

        groups = conn.execute("""
            SELECT group_id,
                   COALESCE(NULLIF(group_name, ''), name)
            FROM student_groups
            ORDER BY 2
        """).fetchall()

    if not teachers or not subjects or not groups:
        st.warning(
            "Please add at least one teacher, one subject "
            "and one student group before creating a session."
        )

    else:
        with st.form("class_session_form", clear_on_submit=True):
            subject = st.selectbox(
                "Subject *",
                subjects,
                format_func=lambda x: x[1]
            )

            teacher = st.selectbox(
                "Teacher *",
                teachers,
                format_func=lambda x: x[1]
            )

            group = st.selectbox(
                "Student Group *",
                groups,
                format_func=lambda x: x[1]
            )

            duration = st.selectbox(
                "Duration (consecutive periods) *",
                [1, 2, 3]
            )

            sessions_per_week = st.number_input(
                "Sessions per week *",
                min_value=1,
                max_value=15,
                value=3
            )

            submitted = st.form_submit_button("➕ Add Class Session")

            if submitted:
                try:
                    with get_connection() as conn:
                        conn.execute("""
                            INSERT INTO class_sessions
                            (subject_id, teacher_id, group_id,
                             duration_periods, sessions_per_week)
                            VALUES (?, ?, ?, ?, ?)
                        """, (
                            subject[0],
                            teacher[0],
                            group[0],
                            duration,
                            sessions_per_week
                        ))

                    st.success("Class session saved successfully!")
                    st.rerun()

                except sqlite3.IntegrityError as e:
                    st.error(f"Could not save session: {e}")

        st.divider()
        st.subheader("📋 Registered Class Sessions")

        with get_connection() as conn:
            sessions = conn.execute("""
                SELECT cs.session_id,
                       COALESCE(NULLIF(s.subject_name, ''), s.name),
                       t.name,
                       COALESCE(NULLIF(g.group_name, ''), g.name),
                       cs.duration_periods,
                       cs.sessions_per_week
                FROM class_sessions cs
                JOIN subjects s ON cs.subject_id = s.subject_id
                JOIN teachers t ON cs.teacher_id = t.teacher_id
                JOIN student_groups g ON cs.group_id = g.group_id
                ORDER BY cs.session_id
            """).fetchall()

        if not sessions:
            st.info("No class sessions added yet.")
        else:
            for sid, subject_name, teacher_name, group_name, duration, weekly in sessions:
                with st.container(border=True):
                    col1, col2 = st.columns([4, 1])

                    with col1:
                        st.write(f"**{subject_name}**")
                        st.caption(f"Teacher: {teacher_name}")
                        st.caption(f"Student Group: {group_name}")
                        st.caption(f"Duration: {duration} consecutive period(s)")
                        st.caption(f"Sessions per week: {weekly}")

                    with col2:
                        if st.button("🗑️ Delete", key=f"del_session_{sid}"):
                            with get_connection() as conn:
                                conn.execute(
                                    "DELETE FROM class_sessions WHERE session_id = ?",
                                    (sid,)
                                )
                            st.rerun()


elif page == "Timetable Generation":
    st.subheader("🧬 Generate University Timetable")
    st.write(
        "Use the Genetic Algorithm to generate a weekly timetable "
        "from your registered classes, teachers, groups and rooms."
    )

    population_size = st.number_input(
        "Population Size",
        min_value=10,
        max_value=200,
        value=30,
        step=10,
    )

    generations = st.number_input(
        "Generations",
        min_value=10,
        max_value=500,
        value=50,
        step=10,
    )

    if st.button("🚀 Generate Timetable", type="primary"):
        try:
            with st.spinner("Generating timetable..."):
                data = load_problem_data()

                if not data["sessions"]:
                    st.error("Add at least one class session first.")
                elif not data["rooms"]:
                    st.error("Add at least one room first.")
                else:
                    result = run_genetic_algorithm(
                        data["sessions"],
                        data["rooms"],
                        population_size=int(population_size),
                        generations=int(generations),
                        time_slots=data["time_slots"],
                        resource_unavailability=data[
                            "resource_unavailability"
                        ],
                    )

                    st.session_state["generated_timetable"] = result
                    st.session_state["timetable_data"] = data

            if (
                "generated_timetable" in st.session_state
                and st.session_state["generated_timetable"] is result
            ):
                if result["is_valid"]:
                    st.success("A timetable candidate passed the hard constraints!")
                else:
                    st.warning(
                        "The algorithm did not find a valid timetable. "
                        "Review the violations before saving."
                    )

        except Exception as exc:
            st.error(f"Timetable generation failed: {exc}")

    result = st.session_state.get("generated_timetable")
    data = st.session_state.get("timetable_data")

    if result is not None and data is not None:
        st.divider()
        st.subheader("📅 Generated Schedule")

        st.metric("Assignments", len(result["best_timetable"]))
        st.metric("Fitness", f"{result['fitness']:.4f}")
        st.metric("Hard-constraint violations", len(result["violations"]))

        session_by_id = {
            session["session_id"]: session
            for session in data["sessions"]
        }
        room_by_id = {room["room_id"]: room for room in data["rooms"]}
        teacher_by_id = {
            teacher["teacher_id"]: teacher
            for teacher in data["teachers"]
        }
        subject_by_id = {
            subject["subject_id"]: subject
            for subject in data["subjects"]
        }
        group_by_id = {
            group["group_id"]: group
            for group in data["groups"]
        }
        slot_by_id = {
            slot["slot_id"]: slot
            for slot in data["time_slots"]
        }

        rows = []

        for assignment in result["best_timetable"]:
            session = session_by_id[assignment["session_id"]]
            start_slot = slot_by_id[assignment["start_slot"]]
            subject = subject_by_id[session["subject_id"]]
            teacher = teacher_by_id[session["teacher_id"]]
            group = group_by_id[session["group_id"]]
            room = room_by_id[assignment["room_id"]]

            rows.append({
                "Day": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"][
                    start_slot["weekday"]
                ],
                "Period": start_slot["period_number"],
                "Duration": session["duration_periods"],
                "Subject": subject["name"],
                "Teacher": teacher["name"],
                "Student Group": group["name"],
                "Room": room["name"],
                "Occurrence": assignment.get("gene_id", ""),
            })

        st.dataframe(rows, use_container_width=True, hide_index=True)

        if result["violations"]:
            with st.expander("View constraint violations"):
                for violation in result["violations"]:
                    st.write(f"- {violation}")

        if result["is_valid"]:
            if st.button("💾 Save Timetable"):
                try:
                    timetable_id = save_timetable(result)
                    st.success(
                        f"Timetable saved successfully! ID: {timetable_id}"
                    )
                except Exception as exc:
                    st.error(f"Could not save timetable: {exc}")


elif page == "Saved Timetables":
    st.subheader("📚 Saved Timetables")
    st.write("View previously generated and saved university timetables.")

    try:
        with get_connection() as conn:
            timetables = conn.execute("""
                SELECT timetable_id, fitness, penalty,
                       generations_run, created_at
                FROM timetables
                ORDER BY timetable_id DESC
            """).fetchall()

        if not timetables:
            st.info("No saved timetables yet. Generate one first.")
        else:
            options = {
                f"Timetable #{tid} | Fitness: {fitness:.4f} | "
                f"Saved: {created_at}": tid
                for tid, fitness, penalty, generations, created_at
                in timetables
            }

            selected_label = st.selectbox(
                "Choose a saved timetable",
                list(options.keys()),
            )
            selected_id = options[selected_label]

            with get_connection() as conn:
                details = conn.execute("""
                    SELECT fitness, penalty, generations_run, created_at
                    FROM timetables
                    WHERE timetable_id = ?
                """, (selected_id,)).fetchone()

                occurrences = conn.execute("""
                    SELECT
                        o.occurrence_number,
                        ts.weekday,
                        ts.period_number,
                        cs.duration_periods,
                        COALESCE(NULLIF(s.subject_name, ''), s.name),
                        t.name,
                        COALESCE(NULLIF(g.group_name, ''), g.name),
                        COALESCE(NULLIF(r.room_name, ''), r.name)
                    FROM timetable_occurrences o
                    JOIN class_sessions cs
                        ON cs.session_id = o.session_id
                    JOIN subjects s
                        ON s.subject_id = cs.subject_id
                    JOIN teachers t
                        ON t.teacher_id = cs.teacher_id
                    JOIN student_groups g
                        ON g.group_id = cs.group_id
                    JOIN rooms r
                        ON r.room_id = o.room_id
                    JOIN time_slots ts
                        ON ts.slot_id = o.start_slot_id
                    WHERE o.timetable_id = ?
                    ORDER BY ts.weekday, ts.period_number,
                             o.occurrence_number
                """, (selected_id,)).fetchall()

            if details:
                fitness, penalty, generations, created_at = details

                col1, col2, col3 = st.columns(3)
                col1.metric("Fitness", f"{fitness:.4f}")
                col2.metric("Penalty", penalty)
                col3.metric("Generations", generations)

                st.caption(f"Created: {created_at}")

            if occurrences:
                day_names = [
                    "Monday", "Tuesday", "Wednesday",
                    "Thursday", "Friday"
                ]

                rows = [
                    {
                        "Day": day_names[weekday],
                        "Period": period,
                        "Duration": duration,
                        "Subject": subject,
                        "Teacher": teacher,
                        "Student Group": group,
                        "Room": room,
                        "Occurrence": occurrence_number,
                    }
                    for (
                        occurrence_number, weekday, period, duration,
                        subject, teacher, group, room
                    ) in occurrences
                ]

                st.dataframe(
                    rows,
                    use_container_width=True,
                    hide_index=True,
                )

                st.success(
                    f"Loaded {len(occurrences)} saved occurrences "
                    f"from timetable #{selected_id}."
                )
            else:
                st.warning(
                    "This timetable has no occurrence records. "
                    "It may be an older timetable saved before "
                    "occurrence storage was introduced."
                )

    except sqlite3.Error as exc:
        st.error(f"Could not load saved timetables: {exc}")
