---
name: persistence
description: PostgreSQL and Redis rules. Use when changing a schema, migration or index, reading EXPLAIN or locks, or designing cache keys. Not for Compose (skill docker).
argument-hint: "[migration | index | tx | backup | diagnose | justify | cache | ratelimit | pubsub | lock] <context>"
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

# Persistence

PostgreSQL (§1–§5) remains the source of truth for inventory, progression and economy; Redis (§6–§9) holds only ephemeral data. Read `references/postgres-18.md` when modeling a schema or local infrastructure and `references/redis-7.md` before pinning a Redis version/license; apply skill `security` to SQL/personal data and skill `docker` (Twelve-Factor) to configuration. Ask before `DROP`, `TRUNCATE` or unbounded `DELETE`.

## 1. Create migrations

Use the next immutable `V<n>__slug.sql` under `src/main/resources/db/migration/`; editing an applied migration is ask-first (`AGENTS.md` Boundaries). Keep one logical change per file and run `CREATE INDEX CONCURRENTLY` outside a transaction.

A migration keeps the previous application release working, so a rollback or a still-running instance survives it: add first (expand), and drop, rename or narrow a column or table in a later release, once no deployed version reads it (contract).

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

## 6. Justify Redis

Record the measured latency/contention/volume Postgres does not solve, whether loss is harmless and behavior when Redis is unavailable. Without a measurement, mark a hypothesis and start without Redis.

## 7. Select an ephemeral use

- Cache: `cache:<type>:<id>`, cache-aside, invalidate on write, always TTL.
- Presence: set/heartbeat with 30–60 second expiry.
- Rate limit: actor/action/window counter with expiry.
- Pub/sub: only for multiple processes; events may be lost.
- Short lock: unique value, `SET NX PX`, compare-and-delete Lua, at most five seconds; never protect economy integrity.
- Light queue: Streams only while its delivery guarantee is sufficient.

## 8. Define failure behavior

Prefix every key with the app/type and set TTL except pub/sub. Use small JSON/hash values, short client timeouts and a circuit breaker/fallback to PostgreSQL. Select eviction (`allkeys-lru` for cache, otherwise `noeviction` plus alert) deliberately.

## 9. Verify

Document key examples, TTL, outage behavior and the metric proving benefit. Test that an unavailable/empty Redis does not corrupt durable state.

Done when: migration is forward-only, indexes have EXPLAIN evidence, transaction/idempotency rules protect effects and backup/lock claims have command output; Redis solves a measured ephemeral need, every stored key has ownership/TTL, outage degrades safely and no durable invariant depends on it.
