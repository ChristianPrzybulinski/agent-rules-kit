# sdd/ — bootstrap de docs/spec

| Arquivo | Escopo |
|---|---|
| `init-spec.sh` | cria `docs/spec/` vazio num repo (features, requirements, decisions, debts), copia `agents/templates/spec-index.md` como `spec.md` inicial e roda `platforms/tools/sync-project.sh` (CI de spec já nasce no projeto) |

Uso: `platforms/kits/sdd/init-spec.sh <repo-dir>`. Processo completo: `agents/skills/process/README.md`.
