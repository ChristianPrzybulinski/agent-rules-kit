---
description: PostgreSQL 17 (17.11 no Docker Hub, ~5 anos de correções, EOL nov/2029, pg_stat_statements no compose do kit). Carregar ao modelar schema ou subir infra local.
trigger: model_decision
verified: "2026-09-29"
sources:
  - https://www.postgresql.org/support/versioning/
---

# PostgreSQL 17

- Versão escolhida para dev local: **17.11** (última minor 17.x no Docker Hub — tag `postgres:17.11`).
- PostgreSQL 17 lançado em 2024-09-26. Política oficial: cada major recebe correções por **~5 anos** após o release; EOL previsto de 17: **nov/2029**. Fonte: https://www.postgresql.org/support/versioning/
- A política recomenda sempre a última minor da major escolhida (minor releases são compatíveis, só bugfixes).
- Imagem: `postgres:17.11` (`library/postgres`, Docker Hub). Compose: `kits/docker/compose.yml` com `pg_stat_statements` pré-carregado.
