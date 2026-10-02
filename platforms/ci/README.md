# platforms/ci/ — schemas and validations

`schemas/`: JSON Schema (draft 2020-12) for kit frontmatter and project `docs/spec/` artifacts. `validations/`: scripts run by `platforms/tools/check.sh` and by kit and project CI.

| Schema | Validates | Target file-name rule |
|---|---|---|
| `knowledge.schema.json` | legacy knowledge-note frontmatter retained for compatibility | `verified` (date) + `sources` (URLs) required |
| `rule.schema.json` | `kit/rules/*.md` | `trigger` is `glob`, `model_decision`, or `manual` |
| `skill.schema.json` | `kit/skills/<name>/SKILL.md` (non-vendor) | `name` = folder; `triggers`; allowed tools |
| `skills-lock.schema.json` | lines of `platforms/kits/third-party/skills.lock` | 40-hex `sha` |
| `spec.schema.json` | a project's `docs/spec/spec.md` | fixed |
| `feature.schema.json` | `docs/spec/features/*.md` | `FEAT-nnn-slug.md` |
| `requirement.schema.json` | `docs/spec/requirements/{functional,non-functional}/*.md` | `REQ-F-nnn-*` / `REQ-NF-nnn-*` |
| `decision.schema.json` | `docs/spec/decisions/*.md` | `DEC-nnn-slug.md` |
| `debt.schema.json` | `docs/spec/debts/*.md` | `DEBT-nnn-slug.md` |

The five spec schemas (`spec`, `feature`, `requirement`, `decision`, `debt`) go to projects **as a copy**: `platforms/tools/sync-project.sh` installs `check_spec.py` and schemas into the project's `.github/spec-lint/`, and `platforms/kits/github/workflows/spec-lint.yml` runs them locally without a kit checkout or token.

| Validation | Scope |
|---|---|
| `validations/check_kit.py` | layout v6, frontmatters, description budget, indexes, links, vendor lock, duplication (`--links` includes `~/.ai-kit/...`) |
| `validations/check_spec.py` | a project's `docs/spec`: schema + id=prefix + FEAT↔REQ cross-check + unique IDs |

Without `pyyaml`/`jsonschema`: structural validation with a WARN; with `CI=1`, their absence is an error.
