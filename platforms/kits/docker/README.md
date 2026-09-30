# kit docker

Local dev stack: PostgreSQL + Redis, and a multi-stage Dockerfile for the Java service.

## Usage

```bash
cp .env.example .env          # fill in POSTGRES_PASSWORD
docker compose -f compose.yml config   # validates
docker compose -f compose.yml up -d
```

- Ports on localhost only (`127.0.0.1:5432`, `127.0.0.1:6379`).
- `postgres:17.11` — latest 17.x on Docker Hub (verified 2026-09-29); `redis:7.4` — latest 7.x minor.
- `init/01-extensions.sql` creates `pg_stat_statements` (enabled via `shared_preload_libraries` in `command`).
- Named volumes `pgdata`/`redisdata` — data survives `down`; `down -v` deletes it.

## Dockerfile.java

`maven:3.9-eclipse-temurin-25` (build) → `eclipse-temurin:25-jre` (runtime). Both tags exist on Docker Hub (verified 2026-09-29). Adjust the `COPY` glob if the project produces more than one jar.
