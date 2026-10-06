---
description: Docker Compose facts for the CLI plugin form (docker compose), the obsolete version field and the v2+ requirement. Load when editing Compose files.
kind: fact
verified: "2026-09-29"
sources:
  - https://docs.docker.com/compose/
  - https://github.com/docker/compose/releases
---

# Docker Compose — v2 vs v5

- Compose became a **CLI plugin** (`docker compose`, with a space) since v2.0; the old `docker-compose` binary (Python, v1) is discontinued/EOL.
- Requirement: Compose v2 or later as the `docker compose` CLI plugin; `docker compose version` must print `v2` or higher. The locally installed release is not recorded here; run `docker compose version` to see it.
- The `version:` field at the top of the compose file is **obsolete** since the Compose spec — omit it (the kit's `compose.yml` doesn't use it).
- Identical commands (`up -d`, `config`, `logs`); only the invocation changes.
- References: https://docs.docker.com/compose/ and release notes at https://github.com/docker/compose/releases.
