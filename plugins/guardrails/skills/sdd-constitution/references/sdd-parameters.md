---
description: The project's sdd parameters in .ai-kit.yaml; each key, its values, its kit default and the step that reads it.
kind: detail
---

# SDD parameters

The kit skills are the process; a project never copies a step to change it. It sets its parameters once, in the `sdd` section of `.ai-kit.yaml` at its git top level, the project profile (KIT-087: `profile.schema.json`, `platforms/tools/profile.py`). `sdd-constitution` writes the section with the keys the project changes; a key left out takes its kind preset or default. The resolver refuses an unknown key or a value outside its range, with or without pyyaml. To see what a step will read, run `PROFILE resolve --section sdd` (`../../session/references/project-profile.md`): it prints the resolved section, every absent key at its preset or default; `check_spec.py --params` prints the same section. Since KIT-087 P4 the `sdd:` block of `docs/spec/spec.md` is not read, and `check_spec.py` fails on one left there; its `review_rounds` and `visual_approval` are `review.rounds` and `evidence.visual_approval`.

A default is the kit's behavior before the key existed, except `max_chain` and `max_feat_tasks`, which the kit did not limit. Kinds (KIT-088): `project.kind` (`business`, the default, `game` or `tooling`) is a preset of defaults no step reads; a key the project sets nowhere takes its kind's preset, else its default. The presets and the profile-only `sdd` keys `vision_sections`, `passes`, `acceptance`, `flow`, `task_table`, `record_when` and `id_prefix.feature`, with `spec_root` and `release.versioning`, are described in `profile.schema.json`. `points` sums the bundled rows' `Complexity`: Low 1, Med 2, High 3.

| Key | Values | Default | Read by |
|---|---|---|---|
| `needs` | `true`, `false` | `true` | the front chain (KIT-075): `false` keeps no NEED file; `sdd-intake` is skipped, `sdd-plan` writes the request, triage and Situations into the FEAT's Problem section, REQs take `source: request <date>` and land with their FEAT, and `check_spec.py` fails a NEED file (`needs-off`: a Markdown file at the top of `needs/`; an empty folder or `NEED-nnn-data/` evidence passes) and a REQ with no FEAT |
| `journeys` | `true`, `false` | on when `docs/spec/journeys/` exists | `sdd-clarify` (journey steps), `sdd-check` (journey links), `sdd-tasks` (journey cells); `check_spec.py` validates `journeys/` by `journey.schema.json`; `spec_trace.py check` needs `traceability.md` when on or once it exists |
| `tracker` | `github`, `none` | `github` | `sdd-tasks` cut (one issue per FEAT, or local `docs/spec/tasks/TASK-nnn.md` items), `sdd-implement`, `sdd-spike` (report destination) |
| `plan_sections` | list of `Design`, `Contract`, `Data`, `UI`, `Assets`, `Flag`, `Tests`, `Observability`, `Risks`, `Dependencies`; `Risks` and `Tests` always | all but `Assets` | `sdd-plan`: the FEAT's `## Plan` subsections |
| `pr_unit` | `task`, `feat` | `task` | `sdd-implement`: one PR per task row or per FEAT |
| `task_minutes` | integer ≥ 1 | `30` | `sdd-tasks`: a row's upper size |
| `row_check` | command or `null` | `null` (the kit's `row_checks.py check FEAT-nnn`, KIT-073) | `sdd-tasks`: runs on the rows before their spec PR; exit 0 required |
| `row_checks` | map: `gates` (the PR-gates JSON), `tests`, `assets`, `protocol`, `artifacts`, `visual`, `evidence_only` (`true` lets a Proof of `evidence:` clauses only pass) | each `null` or `[]`: its rule off; `evidence_only: false` | `row_checks.py`: the inputs of rules c, d, e, h, i, j and k (`sdd-tasks/references/row-checks.md`) |
| `components` | map: component name → its folder, `.` for the root | `{}` (one component) | `row_checks.py` (a row stays in one component; a Files entry may start with a name), `spec_trace.py` (journey test paths) |
| `spec_index` | `true`, `false` | `false` | `spec_trace.py check`: every REQ and journey file has a `spec.md` row, and every row's link resolves |
| `github` | map: `repo` (`null` = the origin remote), `pr_repos`, `aliases` (earlier names PR bodies cite), `blocked_labels`, `progress_labels` | `{repo: null, pr_repos: [], aliases: [], blocked_labels: [blocked], progress_labels: [status:in-progress]}` | `spec_trace.py sync-status` (`tracker: github`): where legacy task issues and closing PRs live; canonical FEAT issues never supply individual row states |
| `cut_command` | command or `null` | `null` (the kit cut, `sdd-tasks` § 4) | `sdd-tasks`: creates/updates one issue per FEAT; a command that emits task issues is incompatible and must not run |
| `max_chain` | integer ≥ 1 | `4` | `sdd-tasks`, `check_spec.py` (fails above it): longest chain of a FEAT's own `Depends on` rows |
| `max_feat_tasks` | integer ≥ 1 | `30` | `sdd-plan` (splits a NEED above it), `check_spec.py` (fails an open `## Versions` block above it, KIT-096; warns on a FEAT without blocks): task rows in one FEAT or version block |
| `release` | `merge`, `manual` | `merge` (delivered once on `main`, flag on or none) | `sdd-review`, `sdd-release` |
| `commits_by` | `executor`, `orchestrator` | `executor` | `sdd-implement`: who commits a task's work |
| `protected_paths` | map: rooted path or glob → label | `{}` | `sdd-tasks` cut (the item gets the label), `review`: a change there needs the label |
| `bundle` | map: `rows` ≥ 1, `points` ≥ 1, `high_rows` ≥ 0 | `{rows: 1, points: 3, high_rows: 1}` | `sdd-tasks` local TASK files only (`tracker: none`): rows sharing a Files path may bundle; never splits a FEAT into GitHub issues |
| `task_cut` (profile) | map: `owned_area_form` (`globs`, `paths`), `required_test_folders` (code glob → test folders), `bundle_exclude` (globs), `longest_chain_max_complexity` (`Low`, `Med`, `High`) | `{owned_area_form: globs, required_test_folders: {}, bundle_exclude: [], longest_chain_max_complexity: Med}` (`High`: no limit) | `sdd-tasks` and `sdd-check` § 1 d: the task cut checklist (`sdd-tasks/references/task-cut.md`, KIT-086) |
| `decision_folding` (profile) | map: `marker` (text) | `{marker: "→ folded into"}` | `sdd-plan` § 5, `sdd-tasks`, `sdd-clarify`, `sdd-review` and `sdd-check` § 1 e: the marker a settled `[DECISION]` line of a FEAT's Open questions gets when it is folded (KIT-086) |
| `migrations` (profile) | list of folders rooted at the repository | `[]` | `spec_trace.py enablers` (`sdd-check` § 1 f, C19): every file under each folder needs an ENB catalog row (`Schema or file`), as `row_checks.protocol.schemas` does for protocol schemas (KIT-095, KIT-087 P2b) |
| `rule_paths` | map: kit rule name → folders, `.` for the whole repository | `{}` (the `stacks` folders) | `sync-project.sh`: the rule's globs and its `AGENTS.md` block |
| `owner_approvals` | list of change kinds, kebab-case | `[decision]` | `review` and an orchestrator under owner-review autonomy: kinds only the owner approves, such as `approved-dec-change`, `protocol-version`, `in-game-evidence` |
| `doc_structure` | map: `enabled` (`true`, `false`), `exempt` (a path in the repository), `headings` (list of `##` to `######` headings), `done_index` (`true`, `false`) | `{enabled: false, exempt: .github/doc-structure-exempt.txt, headings: ["## What goes here", "## What does not go here"], done_index: true}` | `check_docs_structure.py`, run by the `docs.just` `lint` recipe and the spec-tools action, passes as `off` unless enabled (KIT-074) |

Two settings have their own sections: `review.rounds` (integer ≥ 1, default `3`, read by `review`: a ceiling, not a target; the escalation cap for a PR whose fix delta adds a new mechanism, in rounds that end `NOT READY` on one criterion before the owner decides) and `evidence.visual_approval` (`owner`, `reviewer`, `none`; default `none`, `owner` in the game preset; read by `review`: who approves a screen or motion change's captures against its REQ's mock before the merge, and by `row_checks.py` rule j, which is off unless it is `owner` or `reviewer`).

## Rule paths

`sync-project.sh` renders each kit rule under the folders of its stacks (`stacks: {client: godot}`). A rule named
after no profile (`json`, `spec`) covers the folders of every profile that receives it, often the whole repository. A
`rule_paths` entry sets the folders for one rule and wins over the profile; a key that names no kit rule refuses the
sync. For a monorepo whose message schemas live in `game/protocol/`:

```yaml
sdd:
  rule_paths:
    json: [game/protocol]
    godot: [game/client]
```

The sync writes the json rule into a block in `game/protocol/AGENTS.md` (glob `game/protocol/**/*.json`) for runtimes
that load no rule by path, and `--check` flags it when the parameter changes; a missing folder gets no block. Claude
Code gets the rule from the plugin's hook by the kit's own globs, which the parameter does not narrow (KIT-081 stage 3).

A setting with no key here (a model map, a host limit, a formatter) stays in the project's tooling config or `AGENTS.md`; a project-private key in `.ai-kit.yaml` goes under `x-<name>:`, which the kit ignores.
