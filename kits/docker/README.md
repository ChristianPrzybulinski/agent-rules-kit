# kit docker

Stack local de dev: PostgreSQL + Redis, e Dockerfile multi-stage para o serviço Java.

## Uso

```bash
cp .env.example .env          # preencha POSTGRES_PASSWORD
docker compose -f compose.yml config   # valida
docker compose -f compose.yml up -d
```

- Portas só em localhost (`127.0.0.1:5432`, `127.0.0.1:6379`).
- `postgres:17.11` — último 17.x no Docker Hub (verificado 2026-09-29); `redis:7.4` — último menor 7.x.
- `init/01-extensions.sql` cria `pg_stat_statements` (habilitada via `shared_preload_libraries` no `command`).
- Volumes nomeados `pgdata`/`redisdata` — dados sobrevivem a `down`; `down -v` apaga.

## Dockerfile.java

`maven:3.9-eclipse-temurin-25` (build) → `eclipse-temurin:25-jre` (runtime). Ambas as tags existem no Docker Hub (verificado 2026-09-29). Ajuste o glob do `COPY` se o projeto produzir mais de um jar.
