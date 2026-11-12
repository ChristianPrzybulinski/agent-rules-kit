---
name: docker
description: Docker, Compose and Twelve-Factor config. Use when editing compose, Dockerfile, env or deploy config, or fixing a container. Not for data (skill persistence).
argument-hint: "[compose | dockerfile | up | diagnose | config]"
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

# Docker and Twelve-Factor

Use `platforms/kits/docker/compose.yml`; read `references/compose-v2-vs-v5.md` for the Compose v2+ CLI behavior. §1–§4 cover containers; §5–§9 cover the application's own configuration (Twelve-Factor).

## 1. Define Compose services

- Pin image major/minor; never use `latest`.
- Add a healthcheck per service and depend on `service_healthy`.
- Put secrets in ignored `.env` with placeholders in `.env.example`.
- Use named data volumes, read-only init mounts and host binding `127.0.0.1:`.
- Enable `pg_stat_statements` for the local PostgreSQL service.

## 2. Build Java images

Use a multi-stage Maven/Java 25 build and Java 25 JRE runtime, copy only the jar, run as non-root and keep build outputs, `.git` and `.godot` in `.dockerignore`.

## 3. Start and inspect

Run `docker compose up -d --wait`, then `docker compose ps`. On failure inspect `docker compose logs <service>` and execute the service health command.

## 4. Diagnose common failures

- Port conflict → `lsof -i :<port>`.
- Container-to-container connection → service name, not localhost.
- macOS data slowness → named volume instead of bind-mounted database files.
- Disk pressure → `docker system df`; ask before prune.
- `docker compose down -v` destroys data; ask first.

## 5. Externalize configuration

- Put every environment-varying value in an environment variable; `application.yml` contains only safe defaults and `${VAR}` references.
- Version `.env.example` with placeholders/comments and never version `.env`.
- Use typed configuration such as Spring `@ConfigurationProperties`; do not scatter environment lookups through domain code.

## 6. Declare dependencies and backing services

- Declare fixed dependencies in `pom.xml` or `project.godot`; do not rely on machine-installed libraries.
- Attach Postgres, Redis, queues and APIs by URL/credentials from config.
- PostgreSQL remains the source of truth; Redis is cache/ephemeral and the app degrades when it is unavailable.

## 7. Separate build, release and run

Build one immutable jar/export, inject configuration at run time and never edit a production artifact. The same artifact moves between environments.

## 8. Keep processes disposable

- Keep process memory stateless; persist durable state externally.
- Bind the app's own port, stream structured logs to stdout with `correlation_id`, and create no app-managed log file.
- Handle `SIGTERM` with graceful connection closure and transaction completion.

## 9. Preserve parity and admin discipline

- Use the same Postgres/Redis major versions locally and in production; do not substitute H2 for persistence integration tests.
- Run Flyway migrations and admin tasks as versioned commands with the same configuration as the app.
- Scale I/O with processes/virtual threads and CPU work with bounded pools only after measurement.

Done when: images are pinned, services become healthy, data/secrets follow the volume/env rules and the failing container has literal diagnostic output; environment differences are config-only, artifacts are immutable, processes are stateless/disposable, logs stream to stdout, and local service majors match production.
