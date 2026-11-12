---
name: postgresql
description: PostgreSQL persistence rules. Use when changing a schema, migration or index, running EXPLAIN, or diagnosing locks. Not for cache data (skill redis).
argument-hint: "[migration | index | tx | backup | diagnose] <context>"
triggers:
  - user
  - model
allowed-tools:
  - read
  - grep
  - glob
  - exec
  - edit
---

# PostgreSQL

Read `references/postgres-18.md`; apply skill `secure-development` to SQL/personal data and skill `twelve-factor` to configuration. Ask before `DROP`, `TRUNCATE` or unbounded `DELETE`.

## 1. Create migrations

Use the next immutable `V<n>__slug.sql` under `src/main/resources/db/migration/`; never edit an applied migration. Keep one logical change per file and run `CREATE INDEX CONCURRENTLY` outside a transaction.

For a large-table `NOT NULL`, add nullable, backfill, add a `NOT VALID` constraint, validate, then enforce. Use identity or ordered UUID keys, `timestamptz`, and integer smallest units or `numeric` for money—never float.

## 2. Prove indexes

Index foreign keys and measured frequent filters/joins/orders only after `EXPLAIN (ANALYZE, BUFFERS)`. Use composite/partial indexes when the observed plan matches; account for write cost.

## 3. Protect transactions

- Default `READ COMMITTED`; money/inventory uses aggregate `FOR UPDATE` or `SERIALIZABLE` with retry.
- Store an idempotency command key/result in the same transaction as the effect.
- Keep transactions short, order locks consistently and perform no external I/O inside.

## 4. Diagnose

Use `pg_stat_statements`, `pg_stat_activity`, `pg_locks` and table dead-tuple/autovacuum queries. Report the query plan or blocking PID evidence, not a guessed cause.

```sql
EXPLAIN (ANALYZE, BUFFERS) <query>;
SELECT * FROM pg_stat_activity WHERE state <> 'idle';
SELECT * FROM pg_locks WHERE NOT granted;
```

## 5. Back up and verify

Run daily `pg_dump -Fc` and add WAL archiving when RPO is below 24 hours. Test `pg_restore` into an empty database and run a smoke query; keep dumps outside the repository and Docker volume.

Done when: migration is forward-only, indexes have EXPLAIN evidence, transaction/idempotency rules protect effects and backup/lock claims have command output.
