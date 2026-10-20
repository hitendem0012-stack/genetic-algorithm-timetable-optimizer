
def expand_sessions_per_week(sessions):
    """
    Expand each class session into the required number of weekly
    occurrences while preserving the original session ID.

    Each occurrence gets a unique scheduling ID called gene_id.
    """
    expanded = []

    for session in sessions:
        sessions_per_week = session.get("sessions_per_week", 1)

        if (
            not isinstance(sessions_per_week, int)
            or isinstance(sessions_per_week, bool)
            or sessions_per_week < 1
        ):
            raise ValueError(
                f"Session {session['session_id']} has invalid "
                "sessions_per_week."
            )

        for occurrence in range(1, sessions_per_week + 1):
            item = dict(session)
            item["gene_id"] = (
                session["session_id"],
                occurrence,
            )
            expanded.append(item)

    return expanded
