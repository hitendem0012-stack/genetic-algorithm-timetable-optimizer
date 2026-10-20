
import random


def mutate(
    chromosome,
    rooms,
    sessions,
    mutation_rate=0.1,
    time_slots=None,
):
    """Mutate room or start slot while keeping sessions within one day."""

    if not 0 <= mutation_rate <= 1:
        raise ValueError("Mutation rate must be between 0 and 1.")

    mutated = [dict(gene) for gene in chromosome]

    if not rooms and mutated and mutation_rate > 0:
        raise ValueError("At least one room is required.")

    room_ids = [room["room_id"] for room in rooms]
    session_by_id = {
        session["session_id"]: session for session in sessions
    }

    if time_slots is None:
        time_slots = [
            {
                "slot_id": day * 6 + period,
                "weekday": day,
                "period_number": period,
            }
            for day in range(5)
            for period in range(1, 7)
        ]

    position_to_slot = {
        (slot["weekday"], slot["period_number"]): slot["slot_id"]
        for slot in time_slots
    }

    for gene in mutated:
        if random.random() >= mutation_rate:
            continue

        session_id = gene["session_id"]
        session = session_by_id.get(session_id)

        if session is None:
            raise ValueError(f"Unknown session ID: {session_id}")

        duration = session["duration_periods"]

        if (
            not isinstance(duration, int)
            or isinstance(duration, bool)
            or not 1 <= duration <= 6
        ):
            raise ValueError(
                f"Invalid duration for session {session_id}."
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

        can_change_room = bool(room_ids)
        can_change_time = bool(valid_starts)

        if not can_change_room and not can_change_time:
            raise ValueError(
                f"No valid room or time slot for session {session_id}."
            )

        change_room = can_change_room and (
            random.random() < 0.5 or not can_change_time
        )

        if change_room:
            gene["room_id"] = random.choice(room_ids)
        else:
            gene["start_slot"] = random.choice(valid_starts)

    return mutated
