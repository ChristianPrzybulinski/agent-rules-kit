---
id: KIT-068
title: "One FEAT per delivery with fixed Plan sections; sdd-tasks writes the rows, then cuts them; a spec baseline that only shrinks"
status: confirmed
confirmed: "2026-11-14 (owner, chat of the SDD review session: \"e aprovo\" for the split of the redesign into PRs and their order; \"Aprovo todos\" for the six further adjustments, items 3 and 5 here; \"orquestre a implementação de tudo que passamos\" for this run)"
issue: "#243"
pr: "#244"
---

# KIT-068 — Plan sections and one FEAT per delivery; tasks write, then cut; a shrinking spec baseline

## Problem and evidence

[FACT] At `540b6d5` (KIT-067's head), `sdd-plan` § 3 lists what a Plan covers as seven bullets with no sections, so
the `plan_sections` key of KIT-067 has no reader, and § 4 asks for a decision record for any technical choice with a
rejected alternative, even one that matters only inside the FEAT. `sdd-process.md` lists `sdd-to-card` as step 8,
after `review`, while its flow runs it right after `sdd-tasks`. `sdd-tasks` § 6 writes `docs/spec/progress/FEAT-nnn.json`;
`sdd-to-card` cuts one issue per row as `status:proposed` until the architect approves the cut. No step cuts without
GitHub, resyncs rows and items, or bundles rows, and `sdd-parameters.md` marks `tracker`, `task_minutes`, `row_check`,
`cut_command`, `max_chain`, `protected_paths` and `bundle` as read by `sdd-tasks` only once KIT-068 lands.

[FACT] In a consumer project on 2026-11-14 (every `docs/spec/features/*.md` on its default branch, read with
`git show`), 128 FEATs carry a task table: median 12 rows, p90 28, 74 above 10, 12 above 30, and one in-progress FEAT
holds 238 rows. Its 2150 Task cells have a median of 837 characters and 893 exceed 1000. The longest chain of a FEAT's
own `Depends on` rows exceeds 4 rows in 47 of the 128 FEATs (39 rows in the 238-row FEAT). Its 609 REQs have a median
Statement of 74 words (KIT-066). No baseline exists for `check_spec.py` or `sdd-check all`, so a check added later
either fails every old artifact at once, those 47 chains included, or stays off; and an old finding in a report hides
a new one beside it.

[FACT] `plugins/guardrails/rules/godot.md:22` and `sdd-tasks` § 5 ("Generated and build files") put `*.uid`,
`*.import` and `*.translation` in a task's Files, while the kit's own scope gate admits them without an entry once
its config lists them (`platforms/ci/validations/pr_gates.py`, `generated_neighbour`, config key
`generated_neighbours`, code default none, all three in the docstring example and `review-loop/config.example.json`), the Devin playbook
`implement-issue.devin.md:24` lets an executor change them outside Files, and `platforms/kits/godot/.gitignore`
ignores `*.translation`. `godot-standards` `references/scenes-and-generated-files.md:30` repeats the Files rule.

[FACT] Two follow-ups from the #232 review: `templates/spec-journey.md:52` says "a rule no journey uses stays
FEAT-local", stale since KIT-066 made every rule a REQ written before any FEAT; `platforms/kits/github/labels.json`
keeps `status:clarified`, which the FEAT flow no longer reaches, and has no `status:cancelled`.

## Change

- `sdd-plan`: § 2 cuts the NEED into deliveries: one FEAT per delivery, never a bucket FEAT; a NEED of type `platform`
  gets its own FEAT; a delivery estimated above `sdd.max_feat_tasks` rows is split into several FEATs ordered by
  `depends_on`. § 4 writes one `### <section>` per `plan_sections` name (Design, Contract, Data, UI, Flag, Tests,
  Observability, Risks, Dependencies; Risks and Tests always), each with content or `— <why>`; task cells point to
  `Plan § <section>`. § 5 keeps a decision record for a choice with a rejected alternative that outlives the FEAT.
  New references: `references/plan-sections.md` (what each section holds, an example) and `references/contract.md`
  (a field another FEAT reads exists with its value domain; every command has its success reply; one regeneration
  row per consumer; a new message's producer row and its consumer's validator row share a wave).
- `sdd-tasks` (now `exec`) takes the cut and `sdd-to-card` is removed; `references/task-issue.md` moves under it and
  covers both trackers. § 1 gate: a `planned` FEAT (a resync also on `in-progress`). § 2 size rule: one verifiable
  outcome, at most 5 areas, one proof, within `task_minutes`; the Task cell never restates the Plan; dependencies
  explicit only, the longest chain within `max_chain`; above `max_feat_tasks`, back to `sdd-plan`. § 3 writes the
  table (`Status` and `Item` columns) in a spec PR, after `references/row-checks.md` and the project's `row_check`.
  § 4 cuts once that table is approved or merged: `cut_command` when set, else one GitHub issue (`tracker: github`) or
  one `docs/spec/tasks/TASK-nnn-slug.md` (`tracker: none`) per item, bundling new rows of one repository that share a
  Files path within `bundle`, the `protected_paths` label on the item, the `Item` cells and the journeys'
  `Implemented by` / `Proven by` filled. § 5 resync. `references/row-checks.md` (new): the old pre-cut checklist plus
  cited paths in Files or `(read-only)`, wiring in Files, an artifact-policy change cites its decision, protected
  paths, generated neighbours implicit. `references/waves-and-models.md`: High only when the row needs the stronger
  model; a consumer depends on the merged contract, never on the producer; a row on the longest chain is Med at most
  and a High row is split along its Plan steps.
- `platforms/ci/schemas/task.schema.json` and `templates/spec-task.md` (new): `id`, `feat`, `rows`, `title`, `status`
  (`todo|doing|blocked|done|cancelled`), `labels`, `pr`. `spec.schema.json` gains `max_feat_tasks` (integer ≥ 1,
  default 30); `spec-index.md` carries it.
- `platforms/ci/validations/check_spec.py`: every failure carries a rule id (`frontmatter`, `schema`, `id-file`,
  `id-duplicate`, `decision-kinds`, `sdd-params`, `conflict-marker`, `need-link`, `need-status`, `progress`,
  `link-missing`, `link-one-sided`, `req-unlisted`, `task-file`, `task-item`, `task-chain`, `task-cycle`,
  `task-depends`). It validates `tasks/`, checks that TASK files and the rows' `Item` cells name each other, fails an
  open FEAT whose longest own chain exceeds `max_chain`, holds a cycle or names an own row that does not exist, and
  warns above `max_feat_tasks` rows or a Task cell over 1000 characters. `docs/spec/baseline.json`
  (`{"rules": {rule: {artifact: n}}}`) holds old findings, n being their number or, for `task-chain`, the held chain
  length in rows: a held one prints as `BASELINE` and does not block, one above its n fails (a held chain that grows
  included), an n above what is found fails until `--baseline-update` lowers it; `--baseline-init` writes it once;
  `--baseline-against <older.json>` fails an added or raised entry and skips a missing file. `TASK` is a reserved
  decision prefix. `sync-project.sh` copies `task.schema.json`; `check_kit.py` maps the template.
- `platforms/kits/github/workflows/spec-lint.yml`: the checkout fetches full history and a pull request runs step
  `Baseline only shrinks`, `--baseline-against` with the base branch's `docs/spec/baseline.json` when it has one, so
  the file only shrinks in CI and not by convention.
- `sdd-check`: a `BASELINE` or `WARN` line is not a finding; `all` reads `baseline.json` for its rows (`C<n>`, `Q<n>`)
  and lists entries to lower, never to add.
- `rules/godot.md`: generated neighbours go in the source's commit and are never listed in Files (`*.translation`
  stays ignored), so the project's gates config lists them in `generated_neighbours`; `godot-standards` `scenes-and-generated-files.md` and the task issue template say the same.
- `templates/spec-journey.md` note, `labels.json` (proposed, planned, in-progress, validated, delivered, cancelled),
  `templates/spec-feature.md` (Plan sections, `Status` and `Item`), `sdd-process.md`, `rules/spec.md`,
  `sdd-parameters.md`, `sync-profiles.txt`, `platforms/ci/README.md`, `platforms/kits/github/README.md`,
  `platforms/kits/sdd/README.md`, `INDEX.md`.

[DECISION] Design points this change settled, each with its assumption:
- `max_feat_tasks` defaults to 30, just above the consumer's p90 of 28 rows, so it warns on about the largest tenth (12
  of 128 FEATs) and never on a typical one.
- A chain counts rows; `FEAT-nnn T1, T2` belongs to FEAT-nnn up to the next `;`, the form the consumer's cells use.
- The chain, size and cell checks skip `validated`, `delivered` and `cancelled` FEATs (spec-first history); `Item`
  links are checked on every FEAT.
- The baseline counts findings per rule and artifact id, not per message, so rewording a kit message keeps a held
  finding held, and a second finding of the same rule on a held artifact still fails. `task-chain` holds the chain
  length instead (one finding per FEAT), so a held 5-row chain cannot grow to 40; a cycle and a missing row are rules
  of their own.
- A cut item starts ready (`status:planned`, or `status: todo`), since its table was approved before the cut; the
  approve-after-cut label flip goes.
- "Rows of one folder" in the bundle rule reads as rows of one repository, as the consumer's own rule says.
- The row checks other than chain, size and cell stay judgment items, which a project's `row_check` automates.
- `progress/*.json` stays valid for FEATs cut before this change; `sdd-tasks` no longer writes it.

A consumer resyncs (`sync-project.sh`) before writing `max_feat_tasks` or a TASK file: its old schemas refuse both. A
consumer whose old FEATs now fail `task-chain` runs `check_spec.py --baseline-init` once and commits `baseline.json`.
`sync-project.sh` copies `spec-lint.yml` only into a project without one, so a project that keeps its own spec
workflow adds the `Baseline only shrinks` step itself.

Follow-ups, outside this record: `sdd-implement` still orients on `docs/spec/progress/FEAT-nnn.json`, which no step
writes any more (KIT-069 orients by FEAT and item state); `session` `references/handoff-record.md` and
`templates/doc-session-handoff.md` cite the progress file; `pr_gates.py` keeps its own `protected_paths` (KIT-069); a
consumer's adoption (resync, baseline, closing its 238-row FEAT).

## Proof

`bash platforms/tools/check.sh` (also with `CI=1`), `bash platforms/tools/smoke.sh`,
`python3 platforms/ci/validations/check_kit.py --links`, the `test_check_spec`, `test_check_spec_tasks` (new),
`test_spec_trace` and `test_sync_project` suites, and `gitleaks git --redact --log-opts=origin/main..HEAD`. The tests
were committed first (`612dabe`): on the base `540b6d5`, 25 of the 31 new tests fail, and so do the 4 parameter tests
whose fixtures gained `max_feat_tasks`. The 6 that pass guard what must not change: a valid TASK file and a bundled
one pass, a chain at the maximum passes, a delivered FEAT is history, 30 rows do not warn, and another FEAT's rows do
not extend a chain. Results are in the PR body.
The review fix round's tests were committed first too (`ecc1a2c`): on `a7e4d70` all 8 new tests fail (the
`spec-lint.yml` step run against a throwaway git repository, a missing older baseline, a held chain that grows or
shrinks, a missing `Depends on` row), and so do 8 of the 10 changed baseline and cycle tests.

## History

- 2026-11-14: confirmed (owner, chat): the split into KIT-066 to KIT-072 ("e aprovo"), the six further adjustments
  ("Aprovo todos": no bucket FEAT with a WARN-only size key, the shrinking baseline) and this run ("orquestre a
  implementação de tudo que passamos").
- 2026-11-15: review fix round after the coordinator's independent review at `ba3b743` (READY with one major): the
  `spec-lint.yml` template enforces the shrinking baseline on pull requests, `task-chain` holds the chain length,
  cycles and missing `Depends on` rows get rules of their own, and the godot rule names the `generated_neighbours`
  config (orchestrator's design for the major).
