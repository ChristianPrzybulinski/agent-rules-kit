# sdd/ — docs/spec bootstrap

| File | Scope |
|---|---|
| `init-spec.sh` | creates an empty `docs/spec/` in a repo (features, requirements, decisions, debts), copies `templates/spec-index.md` as the initial `spec.md` and runs `platforms/tools/sync-project.sh` (spec CI is born in the project) |

Usage: `platforms/kits/sdd/init-spec.sh <repo-dir>`. Full process: `skills/sdd-constitution/references/sdd-process.md`.
