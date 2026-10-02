---
name: redis
version: "1.1"
description: Redis ephemeral-data rules. Use when designing cache keys/TTL, rate limits, pub/sub or short locks. Not for durable data (skill postgresql).
argument-hint: "[justify | cache | ratelimit | pubsub | lock] <context>"
triggers:
  - user
  - model
allowed-tools:
  - read
  - grep
  - exec
  - edit
---

# Redis

Read `references/redis-7.md` before pinning a version/license. PostgreSQL remains the source of truth for inventory, progression and economy.

## 1. Justify Redis

Record the measured latency/contention/volume Postgres does not solve, whether loss is harmless and behavior when Redis is unavailable. Without a measurement, mark a hypothesis and start without Redis.

## 2. Select an ephemeral use

- Cache: `cache:<type>:<id>`, cache-aside, invalidate on write, always TTL.
- Presence: set/heartbeat with 30–60 second expiry.
- Rate limit: actor/action/window counter with expiry.
- Pub/sub: only for multiple processes; events may be lost.
- Short lock: unique value, `SET NX PX`, compare-and-delete Lua, at most five seconds; never protect economy integrity.
- Light queue: Streams only while its delivery guarantee is sufficient.

## 3. Define failure behavior

Prefix every key with the app/type and set TTL except pub/sub. Use small JSON/hash values, short client timeouts and a circuit breaker/fallback to PostgreSQL. Select eviction (`allkeys-lru` for cache, otherwise `noeviction` plus alert) deliberately.

## 4. Verify

Document key examples, TTL, outage behavior and the metric proving benefit. Test that an unavailable/empty Redis does not corrupt durable state.

Done when: Redis solves a measured ephemeral need, every stored key has ownership/TTL, outage degrades safely and no durable invariant depends on it.
