---
name: docker
version: "1.0"
description: Docker e Compose para ambiente local reproduzível — compose de Postgres/Redis com healthcheck, Dockerfile multi-stage para Java, volumes, redes, .env, diagnóstico. Usar ao criar/alterar infra local, Dockerfile ou quando um serviço não sobe.
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

Base: `platforms/kits/docker/compose.yml` (Postgres + Redis + pgAdmin opcional). Regras: `agents/rules/development/twelve-factor.md`. Verificado nesta máquina: Docker 29.x, Compose v5.x (`docker compose`, não `docker-compose`).

## compose

- Imagens com tag de versão **major.minor** (`postgres:17.x`, `redis:7.x`); nunca `latest`. Mesma major que a produção pretendida.
- `healthcheck` em todo serviço; app depende com `condition: service_healthy`.
- Segredos via `.env` (gitignored) + `.env.example`; nunca inline no yml.
- Volumes nomeados para dados; bind mount só para init scripts (`./infra/postgres/init:/docker-entrypoint-initdb.d:ro`).
- Portas expostas só em `127.0.0.1:` (não `0.0.0.0`).
- `pg_stat_statements` habilitado via `command: postgres -c shared_preload_libraries=pg_stat_statements`.

## dockerfile (Java)

Multi-stage: `maven:3.9-eclipse-temurin-25` build → `eclipse-temurin:25-jre` runtime; usuário não-root; `COPY --from=build target/*.jar app.jar`; `ENTRYPOINT ["java","-XX:+UseContainerSupport","-jar","app.jar"]`. `.dockerignore` com `target/ .git/ .godot/`. Verificar tags existentes no Docker Hub antes de fixar.

## up

```bash
docker compose up -d --wait          # espera healthchecks
docker compose ps                    # estado
docker compose logs -f postgres      # logs
docker compose down                  # mantém volumes
docker compose down -v               # APAGA dados — perguntar antes
```

## diagnose

| Sintoma | Checar |
|---|---|
| serviço `unhealthy` | `docker compose logs <svc>`; healthcheck manual `docker compose exec postgres pg_isready` |
| porta em uso | `lsof -i :5432` |
| sem espaço | `docker system df`; `docker system prune` (perguntar; remove imagens não usadas) |
| app não conecta | host é o **nome do serviço** na rede compose, `localhost` só de fora |
| lento no macOS | volume nomeado em vez de bind mount para dados |

## Veredicto

Serviços · versões fixadas · `docker compose up -d --wait` → saída · não verificado · próximo passo.
