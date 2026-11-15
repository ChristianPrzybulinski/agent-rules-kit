---
description: PostgreSQL schema, index and transaction design and Redis use for a FEAT's Plan § Data. Load when a delivery stores, indexes or caches data.
kind: detail
---

# Data

PostgreSQL stays the source of truth for inventory, progression and economy; Redis holds only ephemeral data. Migration always/never: rule `migrations.md`. Versions and licenses: `postgres-18.md`, `redis-7.md`. SQL and personal data: skill `security` and `security-design.md`; configuration: `twelve-factor.md`. Backup and restore: skill `sdd-release`, reference `backup.md`; diagnosis: skill `investigate`, reference `database.md`.

## 1. Plan the migration

- The next immutable `V<n>__slug.sql` under `src/main/resources/db/migration/` (or the project's tool), one logical change per file; `CREATE INDEX CONCURRENTLY` outside a transaction.
- Expand, then contract: the migration keeps the previous release working, so a rollback or a still-running instance survives it; a drop, rename or narrowing waits for a later release no deployed version reads.
- A large-table `NOT NULL`: add nullable, backfill, add a `NOT VALID` constraint, validate, then enforce.
- Identity or ordered UUID keys, `timestamptz`, integer smallest units or `numeric` for money, never float.

## 2. Prove indexes

Index foreign keys and the measured frequent filters, joins and orders only after `EXPLAIN (ANALYZE, BUFFERS)`. Use a composite or partial index when the observed plan matches it; account for the write cost.

## 3. Protect transactions

- Default `READ COMMITTED`; money and inventory use aggregate `FOR UPDATE` or `SERIALIZABLE` with retry.
- Store an idempotency command key and its result in the same transaction as the effect.
- Keep transactions short, order locks consistently and do no external I/O inside.

## 4. Justify Redis

Record the measured latency, contention or volume PostgreSQL does not solve, whether losing the data is harmless, and the behavior when Redis is unavailable. Without a measurement, mark a `[HYPOTHESIS]` and start without Redis.

## 5. Pick an ephemeral use

- Cache: `cache:<type>:<id>`, cache-aside, invalidate on write, always a TTL.
- Presence: a set or heartbeat with 30-60 second expiry.
- Rate limit: an actor/action/window counter with expiry.
- Pub/sub: only between processes; events may be lost.
- Short lock: unique value, `SET NX PX`, compare-and-delete Lua, at most five seconds; never protects economy integrity.
- Light queue: Streams only while their delivery guarantee is sufficient.

## 6. Define failure behavior

Prefix every key with the app and type and set a TTL (pub/sub excepted). Small JSON or hash values, short client timeouts and a circuit breaker with a fallback to PostgreSQL. Choose eviction deliberately: `allkeys-lru` for a cache, otherwise `noeviction` plus an alert.

## 7. Verify

Plan § Data names the key examples, TTLs, outage behavior and the metric that proves the benefit; Plan § Tests holds a test that an unavailable or empty Redis does not corrupt durable state.

Done when: the migration is forward-only, indexes have EXPLAIN evidence, transaction and idempotency rules protect each effect, Redis solves a measured ephemeral need, every key has an owner and a TTL, an outage degrades safely and no durable invariant depends on Redis.
