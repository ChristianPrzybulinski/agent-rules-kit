# sdd/ — docs/spec bootstrap

| File | Scope |
|---|---|
| `init-spec.sh` | creates an empty `docs/spec/` in a repo (needs, features, requirements, decisions, debts; under the resolved `sdd.flow: feat-only` only features, decisions and debts, KIT-100), copies `plugins/guardrails/templates/spec-index-game.md` (`project.kind: game` in `.ai-kit.yaml`), `spec-index-tooling.md` (`tooling`) or else `spec-index-business.md` as the initial `spec.md`, none with an `sdd:` block (the parameters are the `sdd` section of `.ai-kit.yaml`, KIT-087 P4), and runs `platforms/tools/sync-project.sh` (spec CI is born in the project) |
| `progress.example.json` | example of `docs/spec/progress/FEAT-nnn.json`, the executor progress of a FEAT cut before KIT-068 (`sdd-tasks` now cuts GitHub issues or `TASK-nnn` files); schema `platforms/ci/schemas/progress.schema.json` |

Usage: `platforms/kits/sdd/init-spec.sh <repo-dir>`. Precondition: the repo must already have `AGENTS.md` (the sync generates `CLAUDE.md` importing it). Full process: `plugins/guardrails/skills/sdd-constitution/references/sdd-process.md`.
