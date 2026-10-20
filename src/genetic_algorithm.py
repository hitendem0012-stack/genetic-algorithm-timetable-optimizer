import random

from src.fitness import calculate_fitness
from src.selection import tournament_selection
from src.crossover import crossover
from src.mutation import mutate
from src.session_expander import expand_sessions_per_week

def default_time_slots():
    """Create the project's standard 30 weekday-period slots."""
    return [
        {
            "slot_id": day * 6 + period,
            "weekday": day,
            "period_number": period,
        }
        for day in range(5)
        for period in range(1, 7)
    ]


def create_random_timetable(
    sessions, rooms, max_attempts=100, time_slots=None
):
    """Create one random candidate using valid database slot IDs."""

    if sessions and not rooms:
        raise ValueError("At least one room is required.")

    slots = time_slots if time_slots is not None else default_time_slots()

    position_to_slot = {
        (slot["weekday"], slot["period_number"]): slot["slot_id"]
        for slot in slots
    }

    assignments = []

    for session in sessions:
        duration = session["duration_periods"]

        if (
            not isinstance(duration, int)
            or isinstance(duration, bool)
            or not 1 <= duration <= 6
        ):
            raise ValueError(
                f"Session {session['session_id']} has invalid duration."
            )

        valid_starts = [
            position_to_slot[(day, period)]
            for day in range(5)
            for period in range(1, 7 - duration + 1)
            if all(
                (day, p) in position_to_slot
                for p in range(period, period + duration)
            )
        ]

        if not valid_starts:
            raise ValueError(
                f"No valid starting slot for session {session['session_id']}."
            )

        assignment = {
            "session_id": session["session_id"],
            "start_slot": random.choice(valid_starts),
            "room_id": random.choice(rooms)["room_id"],
        }

        if "gene_id" in session:
            assignment["gene_id"] = session["gene_id"]

        assignments.append(assignment)

    return assignments


def evaluate_timetable(
    assignments,
    sessions,
    rooms,
    time_slots=None,
    resource_unavailability=None,
):
    """Evaluate a candidate against the supplied scheduling constraints."""

    return calculate_fitness(
        assignments,
        sessions,
        rooms,
        time_slots=time_slots,
        resource_unavailability=resource_unavailability,
    )


def generate_initial_population(
    sessions, rooms, population_size=100, time_slots=None
):
    """Generate random timetable candidates."""

    if population_size < 1:
        raise ValueError("Population size must be at least 1.")

    return [
        create_random_timetable(
            sessions, rooms, time_slots=time_slots
        )
        for _ in range(population_size)
    ]


def evolve_population(
    population,
    sessions,
    rooms,
    mutation_rate=0.1,
    crossover_rate=0.8,
    tournament_size=3,
    elite_count=1,
    time_slots=None,
    resource_unavailability=None,
):
    """Create the next generation of candidate timetables."""

    if not population:
        raise ValueError("Population cannot be empty.")

    if not 0 <= mutation_rate <= 1:
        raise ValueError("Mutation rate must be between 0 and 1.")

    if not 0 <= crossover_rate <= 1:
        raise ValueError("Crossover rate must be between 0 and 1.")

    if not 0 <= elite_count <= len(population):
        raise ValueError("Invalid elite count.")

    fitness_scores = [
        evaluate_timetable(
            candidate, sessions, rooms,
            time_slots, resource_unavailability
        )["fitness"]
        for candidate in population
    ]

    ranked_indices = sorted(
        range(len(population)),
        key=lambda index: fitness_scores[index],
        reverse=True,
    )

    next_population = [
        [dict(gene) for gene in population[index]]
        for index in ranked_indices[:elite_count]
    ]

    while len(next_population) < len(population):
        parent1 = tournament_selection(
            population, fitness_scores, tournament_size
        )
        parent2 = tournament_selection(
            population, fitness_scores, tournament_size
        )

        child1, child2 = crossover(
            parent1, parent2, probability=crossover_rate
        )

        for child in (child1, child2):
            child = mutate(
                child,
                rooms,
                sessions,
                mutation_rate=mutation_rate,
                time_slots=time_slots,
            )
            next_population.append(child)

            if len(next_population) >= len(population):
                break

    return next_population


def run_genetic_algorithm(
    sessions,
    rooms,
    population_size=100,
    generations=100,
    mutation_rate=0.1,
    crossover_rate=0.8,
    tournament_size=3,
    elite_count=1,
    time_slots=None,
    resource_unavailability=None,
):
    """Evolve candidates and return the best timetable found."""

    if population_size < 1:
        raise ValueError("Population size must be at least 1.")

    if generations < 0:
        raise ValueError("Generations cannot be negative.")

    if not 0 <= elite_count <= population_size:
        raise ValueError("Invalid elite count.")

    if any("sessions_per_week" in session for session in sessions):
        sessions = expand_sessions_per_week(sessions)

    slots = time_slots if time_slots is not None else default_time_slots()

    population = generate_initial_population(
        sessions, rooms, population_size, time_slots=slots
    )

    best_timetable = None
    best_result = None

    for generation in range(generations + 1):
        results = [
            evaluate_timetable(
                candidate,
                sessions,
                rooms,
                slots,
                resource_unavailability,
            )
            for candidate in population
        ]

        best_index = max(
            range(len(population)),
            key=lambda index: results[index]["fitness"],
        )

        if (
            best_result is None
            or results[best_index]["fitness"] > best_result["fitness"]
        ):
            best_timetable = [
                dict(gene) for gene in population[best_index]
            ]
            best_result = results[best_index]

        if generation < generations:
            population = evolve_population(
                population,
                sessions,
                rooms,
                mutation_rate=mutation_rate,
                crossover_rate=crossover_rate,
                tournament_size=tournament_size,
                elite_count=elite_count,
                time_slots=slots,
                resource_unavailability=resource_unavailability,
            )

    return {
        "best_timetable": best_timetable,
        "fitness": best_result["fitness"],
        "hard_penalty": best_result["hard_penalty"],
        "violations": best_result["violations"],
        "is_valid": best_result["is_valid"],
        "generations": generations,
    }
