
import sys
from pathlib import Path

sys.path.insert(
    0,
    str(Path(__file__).resolve().parents[1])
)

from src.data_loader import load_problem_data


def test_database_data_loads():
    data = load_problem_data()

    assert "teachers" in data
    assert "subjects" in data
    assert "groups" in data
    assert "rooms" in data
    assert "sessions" in data
    assert "time_slots" in data


def test_loaded_sessions_have_required_fields():
    data = load_problem_data()

    for session in data["sessions"]:
        assert "session_id" in session
        assert "teacher_id" in session
        assert "group_id" in session
        assert "duration_periods" in session
        assert "student_count" in session
        assert "requires_lab" in session
