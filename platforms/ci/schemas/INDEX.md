# schemas/ — JSON Schema for frontmatters and specs

| File | Validates |
|---|---|
| `knowledge.schema.json` | `agents/knowledge/**/*.md` |
| `skill.schema.json` | non-vendor `agents/skills/` |
| `skills-lock.schema.json` | `platforms/kits/third-party/skills.lock` |
| `spec.schema.json` | a project's `docs/spec/spec.md` |
| `feature.schema.json` | `docs/spec/features/*.md` |
| `requirement.schema.json` | `docs/spec/requirements/**` |
| `decision.schema.json` | `docs/spec/decisions/*.md` |
| `debt.schema.json` | `docs/spec/debts/*.md` |

Consumed by `../validations/check_kit.py` and `check_spec.py`. Details: `../README.md`.
