---
name: docker
version: "1.0"
description: Docker and Compose for a reproducible local environment — Postgres/Redis compose with healthchecks, multi-stage Dockerfile for Java, volumes, networks, .env, diagnostics. Use when creating/changing local infra, a Dockerfile, or when a service won't start.
argument-hint: "[compose | dockerfile | up | diagnose]"
triggers:
  - user
  - model
allowed-tools:
  - read
  - glob
  - exec
---

# Docker / Compose

Base: `platforms/kits/docker/compose.yml` (Postgres + Redis + optional pgAdmin). Rules: `agents/rules/development/twelve-factor.md`. Verified on this machine: Docker 29.x, Compose v5.x (`docker compose`, not `docker-compose`).

## compose

- Images tagged **major.minor** (`postgres:17.x`, `redis:7.x`); never `latest`. Same major as the intended production.
- `healthcheck` on every service; the app depends with `condition: service_healthy`.
- Secrets via `.env` (gitignored) + `.env.example`; never inline in the yml.
- Named volumes for data; bind mount only for init scripts (`./infra/postgres/init:/docker-entrypoint-initdb.d:ro`).
- Ports exposed only on `127.0.0.1:` (not `0.0.0.0`).
- `pg_stat_statements` enabled via `command: postgres -c shared_preload_libraries=pg_stat_statements`.

## dockerfile (Java)

Multi-stage: `maven:3.9-eclipse-temurin-25` build → `eclipse-temurin:25-jre` runtime; non-root user; `COPY --from=build target/*.jar app.jar`; `ENTRYPOINT ["java","-XX:+UseContainerSupport","-jar","app.jar"]`. `.dockerignore` with `target/ .git/ .godot/`. Check existing tags on Docker Hub before pinning.

## up

```bash
docker compose up -d --wait          # waits for healthchecks
docker compose ps                    # state
docker compose logs -f postgres      # logs
docker compose down                  # keeps volumes
docker compose down -v               # DELETES data — ask first
```

## diagnose

| Symptom | Check |
|---|---|
| `unhealthy` service | `docker compose logs <svc>`; manual healthcheck `docker compose exec postgres pg_isready` |
| port in use | `lsof -i :5432` |
| out of space | `docker system df`; `docker system prune` (ask; removes unused images) |
| app can't connect | host is the **service name** on the compose network, `localhost` only from outside |
| slow on macOS | named volume instead of bind mount for data |

## Verdict

Services · pinned versions · `docker compose up -d --wait` → output · unverified · next step.
