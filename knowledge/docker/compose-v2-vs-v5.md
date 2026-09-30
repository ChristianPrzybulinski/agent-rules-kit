# Docker Compose — v2 vs v5

Verificado: 2026-09-29.

- Compose virou **plugin da CLI** (`docker compose`, com espaço) desde a v2.0; o binário antigo `docker-compose` (Python, v1) está descontinuado/EOL.
- Versão instalada nesta máquina: **Docker Compose v5.5.1** (`docker compose version`).
- O campo `version:` no topo do compose file é **obsoleto** desde Compose spec — omitir (o `compose.yml` do kit não usa).
- Comandos idênticos (`up -d`, `config`, `logs`); apenas a invocação muda.
- Referências: https://docs.docker.com/compose/ e release notes em https://github.com/docker/compose/releases.
