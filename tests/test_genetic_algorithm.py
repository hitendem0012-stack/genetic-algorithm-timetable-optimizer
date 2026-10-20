
import sys
from pathlib import Path

sys.path.insert(
    0,
    str(Path(__file__).resolve().parents[1] / "src")
)

import pytest

from genetic_algorithm import (
    create_random_timetable,
    generate_initial_population,
    evolve_population,
    run_genetic_algorithm,
)


def sample_data():
    sessions = [
        {
            "session_id": 1,
            "duration_periods": 1,
            "teacher_id": 1,
            "group_id": 1,
            "student_count": 30,
            "requires_lab": False,
        },
        {
            "session_id": 2,
            "duration_periods": 2,
            "teacher_id": 2,
            "group_id": 1,
            "student_count": 30,
            "requires_lab": False,
        },
    ]

    rooms = [
        {"room_id": 1, "capacity": 60, "room_type": "Classroom"},
        {"room_id": 2, "capacity": 60, "room_type": "Classroom"},
    ]

    return sessions, rooms


def test_random_timetable_has_one_gene_per_session():
    sessions, rooms = sample_data()

    result = create_random_timetable(sessions, rooms)

    assert len(result) == len(sessions)
    assert {g["session_id"] for g in result} == {1, 2}


def test_population_has_requested_size():
    sessions, rooms = sample_data()

    population = generate_initial_population(
        sessions, rooms, population_size=8
    )

    assert len(population) == 8


def test_evolution_preserves_population_size():
    sessions, rooms = sample_data()
    population = generate_initial_population(
        sessions, rooms, population_size=8
    )

    next_population = evolve_population(
        population, sessions, rooms
    )

    assert len(next_population) == len(population)


def test_run_returns_expected_result_fields():
    sessions, rooms = sample_data()

    result = run_genetic_algorithm(
        sessions,
        rooms,
        population_size=8,
        generations=3,
    )

    assert result["best_timetable"] is not None
    assert "fitness" in result
    assert "hard_penalty" in result
    assert "violations" in result
    assert "is_valid" in result
    assert result["generations"] == 3


def test_empty_sessions_can_be_scheduled():
    result = run_genetic_algorithm(
        [], [], population_size=4, generations=2
    )

    assert result["best_timetable"] == []
    assert result["is_valid"] is True


def test_invalid_population_size_raises_error():
    sessions, rooms = sample_data()

    with pytest.raises(ValueError):
        run_genetic_algorithm(
            sessions, rooms, population_size=0
        )


def test_unavailable_teacher_reduces_fitness():
    from genetic_algorithm import evaluate_timetable

    sessions, rooms = sample_data()

    assignments = [
        {"session_id": 1, "start_slot": 1, "room_id": 1},
        {"session_id": 2, "start_slot": 7, "room_id": 2},
    ]

    slots = [
        {
            "slot_id": day * 6 + period,
            "weekday": day,
            "period_number": period,
        }
        for day in range(5)
        for period in range(1, 7)
    ]

    blocked = [
        {
            "resource_type": "teacher",
            "resource_id": 1,
            "slot_id": 1,
        }
    ]

    normal = evaluate_timetable(assignments, sessions, rooms)
    restricted = evaluate_timetable(
        assignments,
        sessions,
        rooms,
        time_slots=slots,
        resource_unavailability=blocked,
    )

    assert normal["is_valid"] is True
    assert restricted["is_valid"] is False
    assert restricted["fitness"] < normal["fitness"]


def test_genetic_algorithm_accepts_availability_data():
    sessions, rooms = sample_data()

    slots = [
        {
            "slot_id": day * 6 + period,
            "weekday": day,
            "period_number": period,
        }
        for day in range(5)
        for period in range(1, 7)
    ]

    blocked = [
        {
            "resource_type": "teacher",
            "resource_id": 1,
            "slot_id": 1,
        }
    ]

    result = run_genetic_algorithm(
        sessions,
        rooms,
        population_size=8,
        generations=2,
        time_slots=slots,
        resource_unavailability=blocked,
    )

    assert result["best_timetable"] is not None
    assert "violations" in result
    assert result["generations"] == 2


def test_sessions_per_week_creates_unique_occurrences():
    sessions = [
        {
            "session_id": 10,
            "duration_periods": 1,
            "sessions_per_week": 3,
            "teacher_id": 1,
            "group_id": 1,
            "student_count": 30,
            "requires_lab": False,
        }
    ]

    rooms = [
        {"room_id": 1, "capacity": 60, "room_type": "Classroom"}
    ]

    result = run_genetic_algorithm(
        sessions,
        rooms,
        population_size=8,
        generations=2,
    )

    timetable = result["best_timetable"]

    # Three weekly occurrences must be scheduled.
    assert len(timetable) == 3

    # All occurrences belong to the original class session.
    assert all(
        gene["session_id"] == 10
        for gene in timetable
    )

    # Each occurrence must have a unique identity.
    gene_ids = [gene["gene_id"] for gene in timetable]
    assert len(set(gene_ids)) == 3
