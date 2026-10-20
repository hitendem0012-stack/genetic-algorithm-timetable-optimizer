
import sys
from pathlib import Path

# Allow tests to import modules from src/
sys.path.insert(
    0,
    str(Path(__file__).resolve().parents[1] / "src")
)

from constraints import check_hard_constraints


def sample_data():
    sessions = [
        {
            "session_id": 1,
            "teacher_id": 1,
            "group_id": 1,
            "duration_periods": 1,
            "student_count": 40,
            "requires_lab": False
        },
        {
            "session_id": 2,
            "teacher_id": 2,
            "group_id": 2,
            "duration_periods": 1,
            "student_count": 30,
            "requires_lab": False
        }
    ]

    rooms = [
        {
            "room_id": 1,
            "capacity": 60,
            "room_type": "Classroom"
        },
        {
            "room_id": 2,
            "capacity": 40,
            "room_type": "Classroom"
        }
    ]

    return sessions, rooms


def test_valid_schedule_has_no_violations():
    sessions, rooms = sample_data()

    assignments = [
        {"session_id": 1, "start_slot": 1, "room_id": 1},
        {"session_id": 2, "start_slot": 2, "room_id": 2}
    ]

    violations = check_hard_constraints(
        assignments, sessions, rooms
    )

    assert violations == []


def test_teacher_cannot_teach_two_classes_at_once():
    sessions, rooms = sample_data()

    sessions[1]["teacher_id"] = 1

    assignments = [
        {"session_id": 1, "start_slot": 1, "room_id": 1},
        {"session_id": 2, "start_slot": 1, "room_id": 2}
    ]

    violations = check_hard_constraints(
        assignments, sessions, rooms
    )

    assert any("Teacher" in v for v in violations)


def test_room_capacity_is_enforced():
    sessions, rooms = sample_data()

    sessions[0]["student_count"] = 80

    assignments = [
        {"session_id": 1, "start_slot": 1, "room_id": 1}
    ]

    violations = check_hard_constraints(
        assignments, sessions, rooms
    )

    assert any("capacity" in v.lower() for v in violations)


def test_lab_session_requires_lab_room():
    sessions, rooms = sample_data()

    sessions[0]["requires_lab"] = True

    assignments = [
        {"session_id": 1, "start_slot": 1, "room_id": 1}
    ]

    violations = check_hard_constraints(
        assignments, sessions, rooms
    )

    assert any("lab" in v.lower() for v in violations)


def test_student_group_cannot_attend_two_classes_at_once():
    sessions, rooms = sample_data()

    sessions[1]["group_id"] = 1

    assignments = [
        {"session_id": 1, "start_slot": 1, "room_id": 1},
        {"session_id": 2, "start_slot": 1, "room_id": 2}
    ]

    violations = check_hard_constraints(
        assignments, sessions, rooms
    )

    assert any("Student group" in v for v in violations)


def test_room_cannot_host_two_classes_at_once():
    sessions, rooms = sample_data()

    assignments = [
        {"session_id": 1, "start_slot": 1, "room_id": 1},
        {"session_id": 2, "start_slot": 1, "room_id": 1}
    ]

    violations = check_hard_constraints(
        assignments, sessions, rooms
    )

    assert any("Room" in v for v in violations)


def test_multiperiod_session_cannot_cross_day_boundary():
    sessions, rooms = sample_data()

    sessions[0]["duration_periods"] = 2

    assignments = [
        {"session_id": 1, "start_slot": 6, "room_id": 1}
    ]

    violations = check_hard_constraints(
        assignments, sessions, rooms
    )

    assert any("day" in v.lower() or "period" in v.lower()
               for v in violations)


def test_unavailable_teacher_is_reported():
    sessions, rooms = sample_data()
    assignments = [
        {"session_id": 1, "start_slot": 1, "room_id": 1}
    ]
    unavailable = [
        {
            "resource_type": "teacher",
            "resource_id": 1,
            "slot_id": 1,
        }
    ]

    violations = check_hard_constraints(
        assignments,
        sessions,
        rooms,
        resource_unavailability=unavailable,
    )

    assert any("teacher" in v.lower() and "unavailable" in v.lower()
               for v in violations)


def test_unavailable_room_is_reported():
    sessions, rooms = sample_data()
    assignments = [
        {"session_id": 1, "start_slot": 1, "room_id": 1}
    ]
    unavailable = [
        {
            "resource_type": "room",
            "resource_id": 1,
            "slot_id": 1,
        }
    ]

    violations = check_hard_constraints(
        assignments,
        sessions,
        rooms,
        resource_unavailability=unavailable,
    )

    assert any("room" in v.lower() and "unavailable" in v.lower()
               for v in violations)


def test_unavailable_student_group_is_reported():
    sessions, rooms = sample_data()
    assignments = [
        {"session_id": 1, "start_slot": 1, "room_id": 1}
    ]
    unavailable = [
        {
            "resource_type": "group",
            "resource_id": 1,
            "slot_id": 1,
        }
    ]

    violations = check_hard_constraints(
        assignments,
        sessions,
        rooms,
        resource_unavailability=unavailable,
    )

    assert any("group" in v.lower() and "unavailable" in v.lower()
               for v in violations)


def test_custom_slot_ids_are_supported():
    sessions, rooms = sample_data()

    # Slot IDs are intentionally different from 1–30.
    slots = [
        {"slot_id": 101 + day * 10 + period,
         "weekday": day, "period_number": period}
        for day in range(5)
        for period in range(1, 7)
    ]

    assignments = [
        {"session_id": 1, "start_slot": 102, "room_id": 1}
    ]

    violations = check_hard_constraints(
        assignments,
        sessions,
        rooms,
        time_slots=slots,
    )

    assert violations == []
