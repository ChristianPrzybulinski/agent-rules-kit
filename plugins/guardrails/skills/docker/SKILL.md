---
name: docker
description: Docker on a running or remote host - start, inspect, diagnose, deploy. Use when starting, fixing or deploying containers. Not for Compose rules (rule docker).
argument-hint: "[up | diagnose | deploy] [service | host]"
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

# Docker hosts

Operations on a running or remote Docker host. The file rules for Compose files, `Dockerfile*` and `.env.example` are rule `docker.md`, loaded with those files; a service's configuration design (Twelve-Factor) is skill `sdd-plan`, reference `twelve-factor.md`. A repository without a Compose file starts from `~/.ai-kit/platforms/kits/docker/compose.yml`, whose PostgreSQL service preloads `pg_stat_statements`. Compose CLI facts: `references/compose-v2-vs-v5.md`.

## 1. Start and inspect

Run `docker compose up -d --wait`, then `docker compose ps`. On failure, read `docker compose logs <service>` and run the service's health command; paste the literal output.

## 2. Diagnose common failures

- Port conflict → `lsof -i :<port>`.
- Container-to-container connection → the service name, not localhost.
- macOS data slowness → a named volume instead of bind-mounted database files.
- Disk pressure → `docker system df`; ask before any prune.

## 3. Work on a remote host

- Run the same commands against the host the repo `AGENTS.md` or its runbook names (`ssh <host> docker compose ...`, or `DOCKER_HOST=ssh://<user>@<host>`), from the deployment folder it names; read the running state before changing it.
- Before a deploy or an image upgrade on a host that holds data, take and prove a backup (skill `sdd-release`, reference `backup.md`).
- Deploy the pinned, already-built artifact: pull it, `docker compose up -d --wait`, then the runbook's smoke; roll back by redeploying the previous tag. The same artifact moves between environments (`twelve-factor.md` § 3).
- On a remote host, rule `docker`'s data-destroying commands stay the user's too.

Done when: every service is healthy or a failing container has literal diagnostic output, a remote change had its backup first, and no data-destroying command ran as an agent.
