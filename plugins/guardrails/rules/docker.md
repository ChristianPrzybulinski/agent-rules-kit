---
description: Always/never constraints for Compose files, Dockerfiles and .env.example; procedures and running or remote hosts stay in skill docker.
trigger: glob
globs:
  - "**/compose*.yml"
  - "**/compose*.yaml"
  - "**/docker-compose*.yml"
  - "**/docker-compose*.yaml"
  - "**/Dockerfile*"
  - "**/.env.example"
paths:
  - "**/compose*.yml"
  - "**/compose*.yaml"
  - "**/docker-compose*.yml"
  - "**/docker-compose*.yaml"
  - "**/Dockerfile*"
  - "**/.env.example"
---

Always/never for Compose files, `Dockerfile*` and `.env.example`. Operations on a running or remote host: skill `docker`; configuration, backing services and build/release/run design: skill `sdd-plan`, reference `twelve-factor.md`.

- Never: run `docker compose down -v`, `docker volume rm` or `docker system prune`/`docker volume prune` as an agent; they destroy data, so the user runs them (the guard hook denies them).
- Never: a secret value in a Compose file, a Dockerfile (`ENV`, `ARG`, a copied `.env`) or `.env.example`; Compose reads it from the ignored `.env` or a `secrets:` entry, and `.env.example` holds a placeholder.
- Always: a top-level `name:` in the Compose file, so the project name does not follow the folder name; a worktree or a renamed clone would otherwise start its own containers and volumes.
- Always: a `healthcheck` on every long-running service, and `depends_on: {<service>: {condition: service_healthy}}` for a dependency that must be ready.
- Always: pin each image to a major.minor tag (`postgres:18.1`); never `latest` or no tag.
- Always: publish a local service's port on `127.0.0.1:` (`127.0.0.1:5432:5432`) unless the repo `AGENTS.md` says it must be reachable from the network.
- Always: named volumes for data and read-only (`:ro`) mounts for init scripts; never bind-mount a database data directory unless the repo `AGENTS.md` asks for it.
- Always: a Dockerfile builds in stages, copies only the built artifact and runs as a non-root `USER` (a Java image: a Maven build stage and a Java 25 JRE runtime, the jar only); `.git`, build outputs, `.godot` and `.env` stay out through `.dockerignore`.
- Always: every variable a Compose file or the app reads is in `.env.example` with a placeholder or safe default; a new variable lands there in the same commit.
- Always: after an edit, `docker compose config --quiet`, and `docker compose up -d --wait` when the change affects startup; paste the literal output.
