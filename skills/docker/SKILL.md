---
name: docker
description: Docker and Compose workflow. Use when editing compose, a Dockerfile or diagnosing a container that will not start. Not for app config (skill twelve-factor).
argument-hint: "[compose | dockerfile | up | diagnose]"
triggers:
  - user
  - model
allowed-tools:
  - read
  - glob
  - exec
  - edit
---

# Docker and Compose

Use `platforms/kits/docker/compose.yml`; read `references/compose-v2-vs-v5.md` for the installed Compose behavior and `../twelve-factor/SKILL.md` for application configuration.

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

Done when: images are pinned, services become healthy, data/secrets follow the volume/env rules and the failing container has literal diagnostic output.
