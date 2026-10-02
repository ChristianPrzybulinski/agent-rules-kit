---
description: Docker Compose facts for the CLI plugin, obsolete version field and installed v5.5.1. Load when editing Compose files.
kind: fact
verified: "2026-09-29"
sources:
  - https://docs.docker.com/compose/
  - https://github.com/docker/compose/releases
---

# Docker Compose — v2 vs v5

- Compose became a **CLI plugin** (`docker compose`, with a space) since v2.0; the old `docker-compose` binary (Python, v1) is discontinued/EOL.
- Version installed on this machine: **Docker Compose v5.5.1** (`docker compose version`).
- The `version:` field at the top of the compose file is **obsolete** since the Compose spec — omit it (the kit's `compose.yml` doesn't use it).
- Identical commands (`up -d`, `config`, `logs`); only the invocation changes.
- References: https://docs.docker.com/compose/ and release notes at https://github.com/docker/compose/releases.
