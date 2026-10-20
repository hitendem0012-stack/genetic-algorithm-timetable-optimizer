
import sys
from pathlib import Path

sys.path.insert(
    0,
    str(Path(__file__).resolve().parents[1] / "src")
)

import pytest
from selection import tournament_selection, select_parents


def test_tournament_selects_best_of_all_candidates():
    population = ["weak", "medium", "best"]
    scores = [0.1, 0.5, 0.9]

    selected = tournament_selection(
        population, scores, tournament_size=3
    )

    assert selected == "best"


def test_empty_population_raises_error():
    with pytest.raises(ValueError):
        tournament_selection([], [])


def test_mismatched_lengths_raise_error():
    with pytest.raises(ValueError):
        tournament_selection(["A", "B"], [0.5])


def test_tournament_size_must_be_positive():
    with pytest.raises(ValueError):
        tournament_selection(["A"], [0.5], tournament_size=0)


def test_parent_selection_returns_two_candidates():
    population = ["A", "B", "C"]
    scores = [0.2, 0.6, 0.9]

    parent1, parent2 = select_parents(
        population, scores, tournament_size=2
    )

    assert parent1 in population
    assert parent2 in population
