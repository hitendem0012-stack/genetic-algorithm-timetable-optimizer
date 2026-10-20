
import sys
from pathlib import Path

sys.path.insert(
    0,
    str(Path(__file__).resolve().parents[1] / "src")
)

import pytest
from mutation import mutate


def sample_data():
    chromosome = [
        {"session_id": 1, "start_slot": 1, "room_id": 1},
        {"session_id": 2, "start_slot": 7, "room_id": 2},
    ]

    rooms = [
        {"room_id": 1},
        {"room_id": 2},
        {"room_id": 3},
    ]

    sessions = [
        {"session_id": 1, "duration_periods": 1},
        {"session_id": 2, "duration_periods": 2},
    ]

    return chromosome, rooms, sessions


def test_zero_mutation_preserves_chromosome():
    chromosome, rooms, sessions = sample_data()

    result = mutate(
        chromosome, rooms, sessions, mutation_rate=0
    )

    assert result == chromosome
    assert result is not chromosome


def test_mutation_preserves_session_ids():
    chromosome, rooms, sessions = sample_data()

    result = mutate(
        chromosome, rooms, sessions, mutation_rate=1
    )

    assert [g["session_id"] for g in result] == [1, 2]


def test_mutated_start_slots_are_valid():
    chromosome, rooms, sessions = sample_data()

    result = mutate(
        chromosome, rooms, sessions, mutation_rate=1
    )

    for gene in result:
        session = next(
            s for s in sessions
            if s["session_id"] == gene["session_id"]
        )

        start = gene["start_slot"]
        duration = session["duration_periods"]
        period = (start - 1) % 6 + 1

        assert 1 <= start <= 30
        assert period + duration - 1 <= 6


def test_invalid_mutation_rate_raises_error():
    chromosome, rooms, sessions = sample_data()

    with pytest.raises(ValueError):
        mutate(chromosome, rooms, sessions, mutation_rate=1.5)


def test_empty_chromosome():
    assert mutate([], [], [], mutation_rate=0.1) == []


def test_mutation_does_not_modify_original():
    chromosome, rooms, sessions = sample_data()
    original = [dict(gene) for gene in chromosome]

    mutate(chromosome, rooms, sessions, mutation_rate=1)

    assert chromosome == original
