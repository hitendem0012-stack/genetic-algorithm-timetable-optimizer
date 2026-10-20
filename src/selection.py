
import random


def tournament_selection(population, fitness_scores, tournament_size=3):
    """
    Select one candidate using tournament selection.

    population: list of timetable candidates
    fitness_scores: corresponding fitness scores
    tournament_size: number of candidates competing

    Higher fitness score is considered better.
    """

    if not population:
        raise ValueError("Population cannot be empty.")

    if len(population) != len(fitness_scores):
        raise ValueError(
            "Population and fitness_scores must have equal lengths."
        )

    if tournament_size < 1:
        raise ValueError("Tournament size must be at least 1.")

    size = min(tournament_size, len(population))

    candidate_indices = random.sample(
        range(len(population)),
        size
    )

    winner_index = max(
        candidate_indices,
        key=lambda i: fitness_scores[i]
    )

    return population[winner_index]


def select_parents(population, fitness_scores, tournament_size=3):
    """
    Select two parents for crossover.
    """

    parent1 = tournament_selection(
        population, fitness_scores, tournament_size
    )

    parent2 = tournament_selection(
        population, fitness_scores, tournament_size
    )

    return parent1, parent2
