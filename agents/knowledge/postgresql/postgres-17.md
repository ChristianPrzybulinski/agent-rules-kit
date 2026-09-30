---
description: PostgreSQL 17 (17.11 on Docker Hub, ~5 years of fixes, EOL Nov/2029, pg_stat_statements in the kit's compose). Load when modeling a schema or bringing up local infra.
trigger: model_decision
verified: "2026-09-29"
sources:
  - https://www.postgresql.org/support/versioning/
---

# PostgreSQL 17

- Version chosen for local dev: **17.11** (latest 17.x minor on Docker Hub — tag `postgres:17.11`).
- PostgreSQL 17 released on 2024-09-26. Official policy: each major receives fixes for **~5 years** after release; 17's expected EOL: **Nov/2029**. Source: https://www.postgresql.org/support/versioning/
- The policy recommends always the latest minor of the chosen major (minor releases are compatible, bugfixes only).
- Image: `postgres:17.11` (`library/postgres`, Docker Hub). Compose: `kits/docker/compose.yml` with `pg_stat_statements` preloaded.
