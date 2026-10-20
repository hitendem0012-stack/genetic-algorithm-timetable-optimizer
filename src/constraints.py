
from collections import defaultdict


def check_hard_constraints(
    assignments,
    sessions,
    rooms,
    time_slots=None,
    resource_unavailability=None,
):
    """Validate timetable assignments, including repeated occurrences."""

    violations = []
    session_by_id = {s["session_id"]: s for s in sessions}
    room_by_id = {r["room_id"]: r for r in rooms}

    teacher_slots = defaultdict(list)
    group_slots = defaultdict(list)
    room_slots = defaultdict(list)

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

    slot_by_id = {s["slot_id"]: s for s in time_slots}
    position_to_slot = {
        (s["weekday"], s["period_number"]): s["slot_id"]
        for s in time_slots
    }

    unavailable = {
        (row["resource_type"], row["resource_id"], row["slot_id"])
        for row in (resource_unavailability or [])
    }

    seen_genes = set()

    for assignment in assignments:
        session_id = assignment.get("session_id")
        gene_id = assignment.get("gene_id", session_id)
        start_slot = assignment.get("start_slot")
        room_id = assignment.get("room_id")

        if gene_id in seen_genes:
            violations.append(
                f"Occurrence {gene_id}: duplicate assignment."
            )
            continue
        seen_genes.add(gene_id)

        session = session_by_id.get(session_id)
        room = room_by_id.get(room_id)

        if session is None:
            violations.append(f"Unknown session ID: {session_id}")
            continue

        if room is None:
            violations.append(f"Unknown room ID: {room_id}")
            continue

        if start_slot not in slot_by_id:
            violations.append(
                f"Session {session_id}: invalid start slot."
            )
            continue

        duration = session.get("duration_periods")

        if (
            not isinstance(duration, int)
            or isinstance(duration, bool)
            or not 1 <= duration <= 6
        ):
            violations.append(
                f"Session {session_id}: invalid duration."
            )
            continue

        start = slot_by_id[start_slot]
        day = start["weekday"]
        first_period = start["period_number"]

        if first_period + duration - 1 > 6:
            violations.append(
                f"Session {session_id}: exceeds the day's periods."
            )
            continue

        occupied_slots = []

        for period in range(first_period, first_period + duration):
            slot_id = position_to_slot.get((day, period))

            if slot_id is None:
                violations.append(
                    f"Session {session_id}: missing consecutive time slot."
                )
                occupied_slots = []
                break

            occupied_slots.append(slot_id)

        if not occupied_slots:
            continue

        student_count = session.get("student_count")

        if (
            student_count is not None
            and room["capacity"] < student_count
        ):
            violations.append(
                f"Session {session_id}: room capacity is insufficient."
            )

        required_type = session.get("room_type_required")

        if required_type:
            required = required_type.strip().lower()
            actual = room.get("room_type", "").strip().lower()

            if required not in ("any", "either") and required != actual:
                violations.append(
                    f"Session {session_id}: room type '{actual}' "
                    f"does not match required type '{required}'."
                )
        elif session.get("requires_lab", False):
            if "lab" not in room.get("room_type", "").lower():
                violations.append(
                    f"Session {session_id}: requires a lab-compatible room."
                )

        teacher_id = session["teacher_id"]
        group_id = session["group_id"]

        for slot_id in occupied_slots:
            teacher_slots[(teacher_id, slot_id)].append(gene_id)
            group_slots[(group_id, slot_id)].append(gene_id)
            room_slots[(room_id, slot_id)].append(gene_id)

            for resource_type, resource_id in (
                ("teacher", teacher_id),
                ("group", group_id),
                ("room", room_id),
            ):
                if (resource_type, resource_id, slot_id) in unavailable:
                    violations.append(
                        f"Occurrence {gene_id}: {resource_type} "
                        f"{resource_id} is unavailable at slot {slot_id}."
                    )

    def report_overlaps(resource_slots, resource_name):
        for (resource_id, slot_id), gene_ids in resource_slots.items():
            if len(gene_ids) > 1:
                violations.append(
                    f"{resource_name} {resource_id} has a clash "
                    f"at slot {slot_id}: occurrences {gene_ids}"
                )

    report_overlaps(teacher_slots, "Teacher")
    report_overlaps(group_slots, "Student group")
    report_overlaps(room_slots, "Room")

    return violations
