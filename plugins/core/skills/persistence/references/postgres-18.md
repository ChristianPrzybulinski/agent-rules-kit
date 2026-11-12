---
description: PostgreSQL 18 support facts, Docker tag, data-dir change and pg_stat_statements setup. Load when modeling a schema or local infrastructure.
kind: fact
verified: "2026-10-06"
sources:
  - https://www.postgresql.org/support/versioning/
  - https://github.com/docker-library/postgres
---

# PostgreSQL 18

- Version chosen for local dev: **18** (image tag `postgres:18`, `library/postgres` on Docker Hub).
- PostgreSQL 18 released on 2025-09-25. Official policy: each major receives fixes for **~5 years** after release; 18's expected EOL: **Nov/2030**. Source: https://www.postgresql.org/support/versioning/
- The policy recommends always the latest minor of the chosen major (minor releases are compatible, bugfixes only).
- Data dir changed in the 18 image: data lives under `/var/lib/postgresql` (versioned subdir, e.g. `18/docker`); a volume created by a `postgres:17` service at `/var/lib/postgresql/data` is not reused — run `docker compose down -v` once when upgrading. Source: https://github.com/docker-library/postgres
- Compose: `platforms/kits/docker/compose.yml` with `pg_stat_statements` preloaded.
