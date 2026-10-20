# Genetic Algorithm University Timetable Optimizer

Phase 1 starter: SQLite schema and 5-day, 6-period timetable initialization.

Run from project root:

```powershell
python -m database.db
```

Expected: `Database ready! Time slots: 30`

The schema stores each required session as a separate row, with duration from 1 to 6 periods. `time_slots` are base periods; future scheduling will validate the entire occupied block. `subjects.room_type_required` must match a compatible room type.
