---
description: Always/never constraints for database schema migrations; schema, index, transaction and cache design is in the sdd-plan data reference.
trigger: glob
globs:
  - "**/db/migration/**"
  - "**/migrations/**"
paths:
  - "**/db/migration/**"
  - "**/migrations/**"
---

Always/never for schema migrations (PostgreSQL by default). Schema, index, transaction and Redis design: skill `sdd-plan`, reference `data.md`; backup and restore: skill `sdd-release`, reference `backup.md`; a slow query or a lock: skill `investigate`, reference `database.md`.

- Always: a schema change is the next immutable `V<n>__<slug>.sql` (or the project's migration tool's equivalent) with one logical change per file; editing an applied migration is ask-first (`AGENTS.md` Boundaries).
- Always: a migration keeps the previous release working (expand, then contract): add first, and drop, rename or narrow a column or table in a later release, once no deployed version reads it.
- Always: a `NOT NULL` on a large table goes nullable, backfill, a `NOT VALID` constraint, validate, then enforce.
- Always: `CREATE INDEX CONCURRENTLY` runs outside a transaction; an index other than a foreign key's lands with the `EXPLAIN (ANALYZE, BUFFERS)` plan of the query it serves, and a composite or partial index only when that plan matches it.
- Always: identity or ordered UUID keys, `timestamptz`, and integer smallest units or `numeric` for money; never a float for money.
- Always: an idempotency command key and its result are stored in the same transaction as the effect.
- Never: `DROP`, `TRUNCATE` or an unbounded `DELETE` without asking first.
- Never: real personal data in a seed or fixture; e-mail and IP are personal.
