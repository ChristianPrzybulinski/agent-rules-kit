# platforms/ci/ — schemas and validations

`schemas/`: JSON Schema (draft 2020-12) for every kit frontmatter and for the projects' `docs/spec/` artifacts. `validations/`: scripts run by `platforms/tools/check.sh` and by the kit's and projects' CI.

| Schema | Validates | Target file-name rule |
|---|---|---|
| `rule.schema.json` | `agents/rules/**/*.md` | `description` with "Load"/"Use"; `globs` required if `trigger: glob` |
| `knowledge.schema.json` | `agents/knowledge/**/*.md` | `verified` (date) + `sources` (URLs) required |
| `skill.schema.json` | `agents/skills/<type>/<name>/SKILL.md` (non-vendor) | `name` = folder; `version` x.y; `triggers` |
| `skills-lock.schema.json` | lines of `platforms/kits/third-party/skills.lock` | 40-hex `sha` |
| `spec.schema.json` | a project's `docs/spec/spec.md` | fixed |
| `feature.schema.json` | `docs/spec/features/*.md` | `FEAT-nnn-slug.md` |
| `requirement.schema.json` | `docs/spec/requirements/{functional,non-functional}/*.md` | `REQ-F-nnn-*` / `REQ-NF-nnn-*` |
| `decision.schema.json` | `docs/spec/decisions/*.md` | `DEC-nnn-slug.md` |
| `debt.schema.json` | `docs/spec/debts/*.md` | `DEBT-nnn-slug.md` |

The 5 spec ones (`spec`, `feature`, `requirement`, `decision`, `debt`) go to projects **as a copy**: `platforms/tools/sync-project.sh` installs `check_spec.py` + schemas into the project's `.github/spec-lint/`, and the `platforms/kits/github/workflows/spec-lint.yml` workflow runs them locally — no kit checkout or token.

| Validation | Scope |
|---|---|
| `validations/check_kit.py` | layout v4, frontmatters, indexes, links, lock, duplication (`--links` includes `~/.ai-kit/...`) |
| `validations/check_spec.py` | a project's `docs/spec`: schema + id=prefix + FEAT↔REQ cross-check + unique IDs |

Without `pyyaml`/`jsonschema`: structural validation with a WARN; with `CI=1`, their absence is an error.
