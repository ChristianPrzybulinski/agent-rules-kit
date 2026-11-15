---
description: The project's sdd parameters in docs/spec/spec.md; each key, its values, its kit default and the step that reads it.
kind: detail
---

# SDD parameters

The kit skills are the process; a project never copies a step to change it. It sets its parameters once, in the `sdd:`
block of the `docs/spec/spec.md` frontmatter, next to `decision_kinds`. `sdd-constitution` writes the block (the
`spec-index.md` template carries it with every default). `check_spec.py` refuses an unknown key or a value outside its
range, with or without pyyaml; `spec.schema.json` holds the keys, values and defaults. To see what a step will read, run
`python3 .github/spec-lint/check_spec.py --params docs/spec .github/spec-lint/schemas`: it prints the resolved block,
every absent key at its default.

A default is the kit's behavior before the key existed, except `max_chain`, which the kit did not limit. A step marked
KIT-068 or KIT-069 reads its key once that change lands; until then the step's own text decides, and it matches the
default.

| Key | Values | Default | Read by |
|---|---|---|---|
| `needs` | `true`, `false` | `true` | not wired yet (#237): every step keeps `NEED-nnn` files under `needs/`; `false` changes nothing |
| `journeys` | `true`, `false` | on when `docs/spec/journeys/` exists | `sdd-clarify` (journey steps), `sdd-check` (journey links), `sdd-tasks` (journey cells); `sync-project.sh` copies `spec_trace.py` by folder |
| `tracker` | `github`, `none` | `github` | `sdd-tasks` cut (KIT-068), `sdd-implement` (KIT-069), `sdd-spike` (report destination) |
| `plan_sections` | list of `Design`, `Contract`, `Data`, `UI`, `Flag`, `Tests`, `Observability`, `Risks`, `Dependencies`; `Risks` and `Tests` always | all nine | `sdd-plan` (KIT-068): the FEAT's `## Plan` subsections |
| `pr_unit` | `task`, `feat` | `task` | `sdd-implement` (KIT-069): one PR per task row or per FEAT |
| `task_minutes` | integer ≥ 1 | `30` (`sdd-tasks`: 5–30 minutes) | `sdd-tasks` (KIT-068): a row's upper size |
| `row_check` | command or `null` | `null` | `sdd-tasks` (KIT-068): runs on the rows before the cut |
| `cut_command` | command or `null` | `null` (the kit cut, `sdd-to-card` today) | `sdd-tasks` (KIT-068): cuts the approved rows |
| `max_chain` | integer ≥ 1 | `4` | `sdd-tasks` (KIT-068): longest `Depends on` chain in a FEAT |
| `release` | `merge`, `manual` | `merge` (delivered once on `main`, flag on or none) | `sdd-review`, `sdd-release` (KIT-069) |
| `review_rounds` | integer ≥ 1 | `3` (`review` § 4) | `review` (KIT-069): `NOT READY` rounds on one criterion before the owner decides |
| `commits_by` | `executor`, `orchestrator` | `executor` | `sdd-implement` (KIT-069): who commits a task's work |
| `protected_paths` | map: rooted path or glob → label | `{}` | `sdd-tasks` row check (KIT-068), `review` (KIT-069): a change there needs the label |
| `bundle` | map: `rows` ≥ 1, `points` ≥ 1, `high_rows` ≥ 0 | `{rows: 1, points: 3, high_rows: 1}` | `sdd-tasks` cut (KIT-068): rows sharing a Files path in one issue; `rows: 1` = one issue per row |
| `rule_paths` | map: kit rule name → folders, `.` for the whole repository | `{}` (the `--profile` folders) | `sync-project.sh`: the rule's globs and its `AGENTS.md` block |
| `visual_approval` | `owner`, `reviewer`, `none` | `none` | `review` (KIT-069): who approves a screen or motion change's captures against its REQ's mock before the merge |
| `owner_approvals` | list of change kinds, kebab-case | `[decision]` | `review` (KIT-069) and an orchestrator under owner-review autonomy: kinds only the owner approves, such as `approved-dec-change`, `protocol-version`, `in-game-evidence` |

`points` sums the bundled rows' `Complexity`: Low 1, Med 2, High 3.

## Rule paths

`sync-project.sh` renders each kit rule under the folders of its profile (`--profile godot:client`). A rule named
after no profile (`json`, `spec`) covers the folders of every profile that receives it, often the whole repository. A
`rule_paths` entry sets the folders for one rule and wins over the profile; a key that names no kit rule refuses the
sync. For a monorepo whose message schemas live in `game/protocol/`:

```yaml
sdd:
  rule_paths:
    json: [game/protocol]
    godot: [game/client]
```

The sync writes `game/protocol/**/*.json` into `.claude/rules/guardrails-json.md`, and the rule's body into a
generated block in `game/protocol/AGENTS.md`, for runtimes that load no rule by path. `sync-project.sh --check` flags
both when the parameter changes. A folder that does not exist gets no block.

A setting with no key here (a model map, a host limit, a formatter) stays in the project's tooling config or
`AGENTS.md`; the block takes no project-private keys.
