---
description: Compose v2+ virou plugin da CLI (`docker compose`), campo `version:` obsoleto, v5.5.1 instalada. Carregar ao criar/alterar compose ou Dockerfile.
trigger: model_decision
verified: "2026-09-29"
sources:
  - https://docs.docker.com/compose/
  - https://github.com/docker/compose/releases
---

# Docker Compose — v2 vs v5

- Compose virou **plugin da CLI** (`docker compose`, com espaço) desde a v2.0; o binário antigo `docker-compose` (Python, v1) está descontinuado/EOL.
- Versão instalada nesta máquina: **Docker Compose v5.5.1** (`docker compose version`).
- O campo `version:` no topo do compose file é **obsoleto** desde Compose spec — omitir (o `compose.yml` do kit não usa).
- Comandos idênticos (`up -d`, `config`, `logs`); apenas a invocação muda.
- Referências: https://docs.docker.com/compose/ e release notes em https://github.com/docker/compose/releases.
