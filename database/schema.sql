PRAGMA foreign_keys = ON;
CREATE TABLE IF NOT EXISTS teachers (teacher_id INTEGER PRIMARY KEY, name TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS subjects (subject_id INTEGER PRIMARY KEY, name TEXT NOT NULL, room_type_required TEXT NOT NULL DEFAULT 'classroom');
CREATE TABLE IF NOT EXISTS student_groups (group_id INTEGER PRIMARY KEY, name TEXT NOT NULL UNIQUE, student_count INTEGER NOT NULL CHECK(student_count > 0));
CREATE TABLE IF NOT EXISTS rooms (room_id INTEGER PRIMARY KEY, name TEXT NOT NULL UNIQUE, capacity INTEGER NOT NULL CHECK(capacity > 0), room_type TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS class_sessions (session_id INTEGER PRIMARY KEY, subject_id INTEGER NOT NULL REFERENCES subjects(subject_id), teacher_id INTEGER NOT NULL REFERENCES teachers(teacher_id), group_id INTEGER NOT NULL REFERENCES student_groups(group_id), duration_periods INTEGER NOT NULL CHECK(duration_periods BETWEEN 1 AND 6));
CREATE TABLE IF NOT EXISTS time_slots (slot_id INTEGER PRIMARY KEY, weekday INTEGER NOT NULL CHECK(weekday BETWEEN 0 AND 4), period_number INTEGER NOT NULL CHECK(period_number BETWEEN 1 AND 6), UNIQUE(weekday,period_number));
CREATE TABLE IF NOT EXISTS resource_unavailability (id INTEGER PRIMARY KEY, resource_type TEXT NOT NULL CHECK(resource_type IN ('teacher','room','group')), resource_id INTEGER NOT NULL, slot_id INTEGER NOT NULL REFERENCES time_slots(slot_id), UNIQUE(resource_type,resource_id,slot_id));
CREATE TABLE IF NOT EXISTS timetables (timetable_id INTEGER PRIMARY KEY, fitness REAL NOT NULL, penalty REAL NOT NULL, generations_run INTEGER NOT NULL, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS timetable_assignments (timetable_id INTEGER NOT NULL REFERENCES timetables(timetable_id) ON DELETE CASCADE, session_id INTEGER NOT NULL REFERENCES class_sessions(session_id), start_slot_id INTEGER NOT NULL REFERENCES time_slots(slot_id), room_id INTEGER NOT NULL REFERENCES rooms(room_id), PRIMARY KEY(timetable_id,session_id));

-- Stores individual weekly occurrences, including repeated class sessions.
CREATE TABLE IF NOT EXISTS timetable_occurrences (
    occurrence_id INTEGER PRIMARY KEY AUTOINCREMENT,
    timetable_id INTEGER NOT NULL
        REFERENCES timetables(timetable_id) ON DELETE CASCADE,
    session_id INTEGER NOT NULL
        REFERENCES class_sessions(session_id),
    occurrence_number INTEGER NOT NULL CHECK(occurrence_number >= 1),
    start_slot_id INTEGER NOT NULL REFERENCES time_slots(slot_id),
    room_id INTEGER NOT NULL REFERENCES rooms(room_id),
    UNIQUE(timetable_id, session_id, occurrence_number)
);
