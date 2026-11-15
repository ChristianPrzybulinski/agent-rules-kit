# sdd/ — docs/spec bootstrap

| File | Scope |
|---|---|
| `init-spec.sh` | creates an empty `docs/spec/` in a repo (features, requirements, decisions, debts), copies `plugins/guardrails/templates/spec-index.md` as the initial `spec.md`, its `sdd:` process parameters at the kit defaults (KIT-067), and runs `platforms/tools/sync-project.sh` (spec CI is born in the project) |
| `progress.example.json` | example of `docs/spec/progress/FEAT-nnn.json`, the executor progress of a FEAT cut before KIT-068 (`sdd-tasks` now cuts GitHub issues or `TASK-nnn` files); schema `platforms/ci/schemas/progress.schema.json` |

Usage: `platforms/kits/sdd/init-spec.sh <repo-dir>`. Precondition: the repo must already have `AGENTS.md` (the sync generates `CLAUDE.md` importing it). Full process: `plugins/guardrails/skills/sdd-constitution/references/sdd-process.md`.
