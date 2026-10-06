# kit docker

Local dev stack: PostgreSQL + Mailpit (development e-mail), and a multi-stage Dockerfile for the Java service. A Valkey service sits commented in `compose.yml` — uncomment only when a use-case DEC requires a cache.

## Usage

```bash
cp .env.example .env          # fill in POSTGRES_PASSWORD
docker compose -f compose.yml config   # validates
docker compose -f compose.yml up -d
```

- Ports on localhost only (`127.0.0.1:5432`; Mailpit SMTP `127.0.0.1:1025`, UI `127.0.0.1:8025`).
- `postgres:18` — the PG 18 image keeps its data under `/var/lib/postgresql` (versioned subdir); a `postgres:17` volume mounted at `/var/lib/postgresql/data` is not reused — run `docker compose down -v` once when upgrading. `axllent/mailpit:v1.27`. Tags verified on Docker Hub on 2026-10-06.
- `init/01-extensions.sql` creates `pg_stat_statements` (enabled via `shared_preload_libraries` in `command`).
- Named volume `pgdata` — data survives `down`; `down -v` deletes it.

## Dockerfile.java

`maven:3.9-eclipse-temurin-25` (build) → `eclipse-temurin:25-jre` (runtime). Both tags exist on Docker Hub (verified 2026-09-29). Adjust the `COPY` glob if the project produces more than one jar.
