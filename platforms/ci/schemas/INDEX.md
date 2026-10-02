# schemas/ — JSON Schema for frontmatters and specs

| File | Validates |
|---|---|
| `knowledge.schema.json` | legacy knowledge-note frontmatter retained for compatibility |
| `reference.schema.json` | non-vendor `plugins/ai-kit/skills/<name>/references/*.md` |
| `rule.schema.json` | `plugins/ai-kit/rules/*.md` |
| `skill.schema.json` | non-vendor `plugins/ai-kit/skills/<name>/SKILL.md` |
| `skills-lock.schema.json` | `platforms/kits/third-party/skills.lock` |
| `spec.schema.json` | a project's `docs/spec/spec.md` |
| `feature.schema.json` | `docs/spec/features/*.md` |
| `requirement.schema.json` | `docs/spec/requirements/**` |
| `decision.schema.json` | `docs/spec/decisions/*.md` |
| `debt.schema.json` | `docs/spec/debts/*.md` |

Consumed by `../validations/check_kit.py` and `check_spec.py`. Details: `../README.md`.
