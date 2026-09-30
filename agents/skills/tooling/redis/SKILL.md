---
name: redis
version: "1.0"
description: Redis as cache/ephemeral — when to use it (and when not), keys with TTL, pub/sub for presence, rate limiting, short locks; never the source of truth for inventory, progression or economy. Use when proposing cache, session, a light queue or coordination.
argument-hint: "[justify | cache | ratelimit | pubsub | lock] <context>"
triggers:
  - user
  - model
allowed-tools:
  - read
  - grep
  - exec
---

# Redis

Product decision (`[DECISION]`): Redis available **for justified needs**; **never** the source of truth for inventory, progression or economy (that is PostgreSQL). Compose in `platforms/kits/docker/`.

## justify (before using)

Answer in writing in the FEAT/DEC:
1. What measured problem does Postgres not solve? (p95 latency, contention, volume) — no measurement → `[HYPOTHESIS]`, start **without** Redis.
2. Can the data be lost at any moment without inconsistency? If not → it's not Redis.
3. How does the system behave with Redis down? It must degrade, not break.

## Accepted uses

| Use | Structure | TTL | Note |
|---|---|---|---|
| Read cache (static content, profile) | `STRING`/`HASH` `cache:<type>:<id>` | yes, always | invalidate on write; cache-aside |
| Presence/online | `SET` per map + `EXPIRE` renewed by heartbeat | 30-60 s | source is the connection, Redis is a reflection |
| Rate limit | `INCR` + `EXPIRE` per `<actor>:<action>:<window>` | window | sliding window if precision is needed |
| Pub/sub between server instances | channel per map/region | — | only if >1 process; otherwise in-memory |
| Short lock | `SET key val NX PX <ms>` + release by Lua script comparing `val` | ≤ 5 s | never for an economy invariant (that is `FOR UPDATE` in PG) |
| Light queue | `XADD`/Streams | — | reevaluate if a strong guarantee is needed |

## Rules

- Every key has a `<app>:<type>:` prefix and a TTL (except pub/sub). No TTL = leak.
- Serialization: small JSON or `HASH`; never a Java serialized object.
- Config `maxmemory-policy allkeys-lru` (cache) or `noeviction` + alert (if something cannot evaporate — then question whether it's Redis).
- Client: Lettuce (Spring Data Redis default); short timeout; circuit breaker (Resilience4j) → fallback to PG.

## Verdict

Proposed use · justification (measured or `[HYPOTHESIS]`) · behavior without Redis · keys/TTL · unverified · next step.
