
import sys
from pathlib import Path

sys.path.insert(
    0,
    str(Path(__file__).resolve().parents[1] / "src")
)

import pytest
from crossover import single_point_crossover, crossover


def sample_parents():
    parent1 = [
        {"session_id": 1, "start_slot": 1, "room_id": 1},
        {"session_id": 2, "start_slot": 2, "room_id": 1},
        {"session_id": 3, "start_slot": 3, "room_id": 2},
        {"session_id": 4, "start_slot": 4, "room_id": 2},
    ]

    parent2 = [
        {"session_id": 1, "start_slot": 7, "room_id": 2},
        {"session_id": 2, "start_slot": 8, "room_id": 2},
        {"session_id": 3, "start_slot": 9, "room_id": 1},
        {"session_id": 4, "start_slot": 10, "room_id": 1},
    ]

    return parent1, parent2


def test_children_keep_all_session_ids():
    parent1, parent2 = sample_parents()

    child1, child2 = single_point_crossover(parent1, parent2)

    expected_ids = [1, 2, 3, 4]

    assert [g["session_id"] for g in child1] == expected_ids
    assert [g["session_id"] for g in child2] == expected_ids


def test_crossover_with_one_gene():
    parent1 = [{"session_id": 1, "start_slot": 1, "room_id": 1}]
    parent2 = [{"session_id": 1, "start_slot": 7, "room_id": 2}]

    child1, child2 = single_point_crossover(parent1, parent2)

    assert child1 == parent1
    assert child2 == parent2


def test_empty_parents_return_empty_children():
    assert single_point_crossover([], []) == ([], [])


def test_different_parent_lengths_raise_error():
    parent1 = [{"session_id": 1, "start_slot": 1, "room_id": 1}]
    parent2 = []

    with pytest.raises(ValueError):
        single_point_crossover(parent1, parent2)


def test_probability_zero_preserves_parents():
    parent1, parent2 = sample_parents()

    child1, child2 = crossover(parent1, parent2, probability=0)

    assert child1 == parent1
    assert child2 == parent2


def test_invalid_probability_raises_error():
    parent1, parent2 = sample_parents()

    with pytest.raises(ValueError):
        crossover(parent1, parent2, probability=1.5)
