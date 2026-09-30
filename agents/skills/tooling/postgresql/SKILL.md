---
name: postgresql
version: "1.0"
description: PostgreSQL as the source of truth — modeling, Flyway migrations, indexes, transactions/isolation, idempotency, backup/restore and diagnostics (EXPLAIN, locks, bloat). Use when creating/changing a schema, investigating slowness or planning persistence.
argument-hint: "[migration | index | tx | backup | diagnose] <context>"
triggers:
  - user
  - model
allowed-tools:
  - read
  - grep
  - glob
  - exec
---

# PostgreSQL

Rules: `agents/rules/development/twelve-factor.md` (backing service), `agents/rules/security/secure-development.md` (parameterized SQL, personal data). Local compose in `platforms/kits/docker/`. Never run a destructive command (`DROP`, `TRUNCATE`, `DELETE` without `WHERE`) without explicit authorization.

## migration (Flyway)

- File `V<n>__<slug>.sql` in `src/main/resources/db/migration/`; sequential `n`; **never** edit an already-applied migration (create a corrective `V<n+1>`).
- One logical change per migration. `CREATE INDEX CONCURRENTLY` outside a transaction (`-- flyway:executeInTransaction=false`).
- New column on a large table: `ADD COLUMN ... DEFAULT` is fast (PG ≥11); `NOT NULL` in two steps (add → backfill → `NOT VALID` constraint → `VALIDATE`).
- Keys: `bigint generated always as identity` or `uuid` (v7 if ordering matters). `timestamptz`, never `timestamp`.
- Money/game currency: `bigint` in the smallest unit or `numeric`; never `float`.

## index

- An index for each FK and for columns in frequent `WHERE`/`JOIN`/`ORDER BY` — proven by `EXPLAIN (ANALYZE, BUFFERS)`, not by intuition.
- Partial (`WHERE deleted_at IS NULL`) and composite (order = selectivity + usage) when the plan shows it.
- Do not index "just in case": every index costs writes.

## tx (transactions)

- Default `READ COMMITTED`; an economy/inventory operation → `SELECT ... FOR UPDATE` on the aggregate or `SERIALIZABLE` with retry.
- Idempotency: table `processed_commands(command_id pk, result, created_at)`; insert in the same transaction as the effect.
- Short transaction; never external I/O (HTTP, game network) inside it.
- Deadlock → order locks consistently (by ascending id).

## backup

- Daily `pg_dump -Fc` + WAL archiving if RPO < 24h. Test the **restore** (`pg_restore` into an empty database + smoke query) — an untested backup does not exist.
- Dump never in the repo; locally outside the Docker volume.

## diagnose

```sql
EXPLAIN (ANALYZE, BUFFERS) <query>;
SELECT * FROM pg_stat_activity WHERE state <> 'idle';
SELECT * FROM pg_locks l JOIN pg_stat_activity a USING (pid) WHERE NOT granted;
SELECT relname, n_dead_tup, last_autovacuum FROM pg_stat_user_tables ORDER BY n_dead_tup DESC LIMIT 10;
```
`pg_stat_statements` enabled in the local compose to find expensive queries.

## Verdict

What was done · migration created (`V<n>`) · proof (`./mvnw flyway:info`/integration test) · unverified · next step.
