---
description: Twelve-Factor App applied to Java services and local tools — per-environment config, stateless processes, logs as a stream, dev/prod parity. Load when configuring an application, Docker, variables or deploy.
trigger: model_decision
---

# Twelve-Factor (what applies here)

| Factor | Practical rule |
|---|---|
| I. Codebase | 1 repo per app (or monorepo with modules); same base in every environment. |
| II. Dependencies | Declared in `pom.xml`/`project.godot`; no lib installed "on the machine". Fixed versions, no ranges. |
| III. Config | Everything that varies per environment comes from an environment variable. `application.yml` only has safe defaults and `${VAR}`. `.env.example` versioned; `.env` never. |
| IV. Backing services | Postgres, Redis, queues = resources attached by URL. Swapping local for cloud = change env, not code. |
| V. Build, release, run | Immutable artifact (jar, Godot export). Config injected at run. Never edit an artifact in production. |
| VI. Processes | Stateless. Session and game state persist in Postgres (source of truth) or Redis (cache/ephemeral, never source of truth for inventory/economy). |
| VII. Port binding | App exposes its own port; no dependency on an external servlet container. |
| VIII. Concurrency | Scale by process; JVM: virtual threads for I/O, fixed pool for CPU. |
| IX. Disposability | Fast start, graceful shutdown (`SIGTERM` → closes connections, finishes transactions). |
| X. Dev/prod parity | Same Postgres/Redis (major version) locally via Compose and in production. No H2 "just for tests". |
| XI. Logs | Stream to stdout, structured JSON, with `correlation_id`. No app-managed log file. |
| XII. Admin processes | Migrations (Flyway) and admin tasks as versioned commands, running with the same config. |

## Condition → action

- New configurable parameter → `@ConfigurationProperties` + entry in `.env.example` with a comment + safe default.
- Secret → env/keychain; never in yml, code or log.
- New external dependency (database, queue, API) → URL/credential via env + service in `docker-compose.yml`.
