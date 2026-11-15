---
description: "PostgreSQL evidence for a slow query, a lock or table bloat: the queries that show the plan, the blocker or the dead tuples."
kind: detail
---

# Database evidence

§ 3 of `investigate` when the symptom sits in PostgreSQL. Report the query plan, the blocking PID or the counter, never a guessed cause. Schema and index design: skill `sdd-plan`, reference `data.md`.

```sql
EXPLAIN (ANALYZE, BUFFERS) <query>;                 -- the executed plan, with row estimates and buffers
SELECT * FROM pg_stat_activity WHERE state <> 'idle';  -- what runs now, and for how long
SELECT * FROM pg_locks WHERE NOT granted;           -- who waits; join pg_stat_activity on pid for the blocker
SELECT relname, n_dead_tup, last_autovacuum FROM pg_stat_user_tables ORDER BY n_dead_tup DESC LIMIT 10;
```

- `pg_stat_statements` ranks the queries by total time; it needs the extension preloaded (the kit's Compose file does).
- `EXPLAIN (ANALYZE, ...)` runs the statement: wrap a write in `BEGIN; ... ROLLBACK;`.
- A lock explanation needs the blocking and the blocked PID from the same snapshot; a race needs a concurrent test or trace.

Done when: the report quotes the plan, the blocking PID or the counter that shows the cause.
