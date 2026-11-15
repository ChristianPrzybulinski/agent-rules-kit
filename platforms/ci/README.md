# platforms/ci/ — schemas and validations

`schemas/`: JSON Schema (draft 2020-12) for kit frontmatter and project `docs/spec/` artifacts. `validations/`: scripts run by `platforms/tools/check.sh` and by kit and project CI.

| Schema | Validates | Target file-name rule |
|---|---|---|
| `agent.schema.json` | shared Devin/Claude profiles under `plugins/*/agents/` | lowercase and Claude tool lists map 1:1 |
| `knowledge.schema.json` | legacy knowledge-note frontmatter retained for compatibility | `verified` (date) + `sources` (URLs) required |
| `rule.schema.json` | `plugins/*/rules/*.md` | `trigger` is `glob`, `model_decision`, or `manual` |
| `skill.schema.json` | `plugins/*/skills/<name>/SKILL.md` (non-vendor) | `name` = folder; `triggers`; allowed tools |
| `skills-lock.schema.json` | lines of `platforms/kits/third-party/skills.lock` | 40-hex `sha` |
| `spec.schema.json` | a project's `docs/spec/spec.md` | fixed; optional `decision_kinds` (kind → decision id prefix) and `sdd` (the project's process parameters with their defaults, KIT-067) |
| `feature.schema.json` | `docs/spec/features/*.md` | `FEAT-nnn-slug.md` |
| `requirement.schema.json` | `docs/spec/requirements/{functional,non-functional}/*.md` | `REQ-F-nnn-*` / `REQ-NF-nnn-*`; optional `status` (`proposed`, `approved`, `retired`) |
| `decision.schema.json` | `docs/spec/decisions/*.md` | `DEC-nnn-slug.md`, or `<PREFIX>-nnn-slug.md` with the `kind` whose prefix `spec.md` `decision_kinds` declares |
| `debt.schema.json` | `docs/spec/debts/*.md` | `DEBT-nnn-slug.md` |
| `need.schema.json` | `docs/spec/needs/*.md` | `NEED-nnn-slug.md`; `type` and `status` enums, forward links only |
| `journey.schema.json` | `docs/spec/journeys/*.md` | `J-NN[-slug].md` |
| `task.schema.json` | `docs/spec/tasks/*.md`, one cut item per file when `sdd.tracker` is `none` (KIT-068) | `TASK-nnn-slug.md`; `feat`, `rows`, `status` (`todo`, `doing`, `blocked`, `done`, `cancelled`) |
| `progress.schema.json` | `docs/spec/progress/FEAT-nnn.json`, kept for FEATs cut before KIT-068 | `FEAT-nnn.json`, equal to its `feat` |

The nine spec schemas (`spec`, `feature`, `requirement`, `decision`, `debt`, `need`, `task`, `journey`, `progress`) go to projects **as a copy**: `platforms/tools/sync-project.sh` installs `check_spec.py` and schemas into the project's `.github/spec-lint/`, and `platforms/kits/github/workflows/spec-lint.yml` runs them locally without a kit checkout or token. `journey.schema.json` and `spec_trace.py` are installed only when the project has `docs/spec/journeys/`.

| Validation | Scope |
|---|---|
| `validations/check_kit.py` | multi-plugin layout, manifests and dependency graph, frontmatters, description budget, README completeness and `INDEX.md` placement (self-test `validations/test_check_kit_readmes.py`), links, vendor lock, duplication (`--links` includes `~/.ai-kit/...`) |
| `validations/check_spec.py` | a project's `docs/spec`: schema + id=prefix + FEAT↔REQ cross-check (ids exist, both frontmatters list each link; a REQ with no FEAT must be listed by an open NEED) + NEED forward links (each listed id exists with its kind; `refined`/`delivered` backed by links, `delivered` only with delivered FEATs or, for a `decision` NEED with no FEAT, an approved decision) + unique IDs + `progress/*.json` (schema, feat exists, name = feat, unique task ids) + the `spec.md` `sdd` block checked against `spec.schema.json` with or without pyyaml; `--params <spec-dir> <schemas-dir>` prints that block resolved, every absent key at its default (KIT-067) + `tasks/TASK-nnn` files and the FEAT rows' `Item` cells naming each other, an open FEAT's longest own `Depends on` chain within `sdd.max_chain`, no cycle and no own id that is not a row, a WARN above `sdd.max_feat_tasks` rows or a 1000-character Task cell + `baseline.json` (KIT-068): every failure carries a rule id, old findings held per rule and artifact (a count, or for `task-chain` the held chain length) print as `BASELINE` and do not block, the file only shrinks (`--baseline-init` once, `--baseline-update` lowers, `--baseline-against <older.json>` fails an added or raised entry and skips a missing file; the `spec-lint.yml` template runs it on every pull request); self-tests `validations/test_check_spec.py`, `validations/test_check_spec_tasks.py` |
| `validations/spec_trace.py` | a project's `docs/spec/journeys/`: step-table link checks, FEAT↔REQ symmetry, `traceability.md` generation/staleness, `impact`/`mark-done`/`status`; self-test `validations/test_spec_trace.py` |
| `validations/pr_gates.py` | the no-model PR gates against the GitHub REST API, driven by a project JSON config; served by `platforms/kits/github/workflows/pr-contract.yml` |

Without `pyyaml`/`jsonschema`: structural validation with a WARN; with `CI=1`, their absence is an error.
