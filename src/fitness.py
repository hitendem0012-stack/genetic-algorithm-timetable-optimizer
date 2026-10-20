
from src.constraints import check_hard_constraints


def calculate_fitness(
    assignments,
    sessions,
    rooms,
    time_slots=None,
    resource_unavailability=None,
):
    """
    Calculate timetable fitness.

    Fewer hard constraint violations = higher fitness.
    A timetable with zero hard violations receives fitness 1.0.
    """

    violations = check_hard_constraints(
        assignments=assignments,
        sessions=sessions,
        rooms=rooms,
        time_slots=time_slots,
        resource_unavailability=resource_unavailability,
    )

    hard_penalty = len(violations) * 100

    # Higher fitness means fewer hard-constraint violations.
    fitness = 1 / (1 + hard_penalty)

    return {
        "fitness": fitness,
        "hard_penalty": hard_penalty,
        "violations": violations,
        "is_valid": len(violations) == 0,
    }
