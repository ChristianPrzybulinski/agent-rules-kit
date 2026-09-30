# schemas/ — JSON Schema de frontmatters e specs

| Arquivo | Valida |
|---|---|
| `rule.schema.json` | `agents/rules/**/*.md` |
| `knowledge.schema.json` | `agents/knowledge/**/*.md` |
| `skill.schema.json` | `agents/skills/` não-vendor |
| `skills-lock.schema.json` | `platforms/kits/third-party/skills.lock` |
| `spec.schema.json` | `docs/spec/spec.md` de projeto |
| `feature.schema.json` | `docs/spec/features/*.md` |
| `requirement.schema.json` | `docs/spec/requirements/**` |
| `decision.schema.json` | `docs/spec/decisions/*.md` |
| `debt.schema.json` | `docs/spec/debts/*.md` |

Consumidos por `../validations/check_kit.py` e `check_spec.py`. Detalhes: `../README.md`.
