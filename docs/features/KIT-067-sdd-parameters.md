---
id: KIT-067
title: "A project sets its process in an sdd: block; the constitution writes it with the glossary, areas and REVIEW.md; each folder's AGENTS.md carries its rules"
status: confirmed
confirmed: "2026-11-14 (owner, chat of the SDD review session: \"aprovo\" for the split and order of KIT-066 to KIT-071, \"aprovo e pode começar em paralelo\" to start this change beside KIT-071)"
issue: "#234"
pr: ""
---

# KIT-067 — Project sdd: parameters, constitution outputs and rule blocks per folder

## Problem and evidence

[FACT] At `46c2602` (KIT-066's head) the kit's process limits are prose inside each step: `sdd-tasks` sizes a row at
"roughly 5–30 minutes, at most five named files", `review` § 4 stops after three `NOT READY` rounds on one criterion,
`sync-project.sh` copies the journey validator when `docs/spec/journeys/` exists, and `spec.schema.json` lets
`docs/spec/spec.md` declare only `decision_kinds` (KIT-064). The review gate script keeps its own `protected_paths`
(label → globs) in a separate JSON config (`review/references/pr-gates.md`).

[FACT] In a consumer project, the owner's analysis of 2026-11-14 classifies the architect guide's 71 parts and 167
rules restated by its loop prompts; no prompt names a kit skill. The parts it files as parameters are bundle limits
(3 rows, 6 points, one High), a row checker before the cut, rows sized for 1–2 h, three rounds per kind before the
owner and who commits (executor or orchestrator). Each is a kit rule with a project value, so today the project copies
the rule to change the value.

[FACT] `sdd-constitution` wrote `AGENTS.md` and an index with an empty glossary. KIT-066 made `sdd-clarify` require
every domain term a REQ uses in the `spec.md` glossary, and the consumer's glossary held 21 terms on 2026-11-14, about
half of them process terms. Nothing wrote the architecture areas the approved task size rule counts (≤ 5 areas per
row). `platforms/kits/github/REVIEW.md` lists 13 criteria without the skill section that holds each rule, and no step
wrote a project's copy.

[FACT] `sync-project.sh` scopes a rule's globs only through `--profile <name>:<dir>`; a rule named after no profile
(`json`, `spec`) takes every profile folder or the whole repository (`test_multi_profile_union_and_folder_scope`
asserts `**/*.json` stays whole with a root `docs` profile), so a monorepo cannot send the JSON rule to its protocol
folder alone.

[FACT] Codex loads no rule by path; the README's platform table has it read `.claude/rules/` on the `AGENTS.md`
Boundaries line. The 30-day measurement recorded in the owner's design notes of 2026-11-14 found Codex opened the
godot rule in 0 of 18 sessions that edited `.gd` files and the java rule in 3 of 6, while it read the
`godot-standards` skill in 18 of 18. Claude Code loads a path rule on a Read, Write or Edit of a match.

## Change

- `platforms/ci/schemas/spec.schema.json`: optional `sdd`, a map with a `default` and a reader for each key: `needs`
  (`true`), `journeys` (absent = on when `journeys/` exists), `tracker` (`github|none`, `github`), `plan_sections`
  (subset of Design, Contract, Data, UI, Flag, Tests, Observability, Risks, Dependencies; `Risks` and `Tests` required;
  all nine), `pr_unit` (`task|feat`, `task`), `task_minutes` (`30`), `row_check` and `cut_command` (command or
  `null`), `max_chain` (`4`), `release` (`merge|manual`, `merge`), `review_rounds` (`3`), `commits_by`
  (`executor|orchestrator`, `executor`), `protected_paths` (path or glob → label, `{}`), `bundle` (`rows` 1, `points` 3,
  `high_rows` 1: one issue per row) and `rule_paths` (kit rule → folders, `{}`). An unknown key fails.
- `platforms/ci/validations/check_spec.py`: checks the block against that schema in full and structural mode alike,
  each failure naming its key (`sdd.tracker 'jira' is not one of ['github', 'none']`); `--params <spec-dir>
  <schemas-dir>` prints the resolved block as JSON, every absent key at its default. The structural parser now reads
  maps nested by indentation, nested flow lists and maps, booleans and negative integers, so a project without pyyaml
  can carry the block. `test_check_spec.py` adds `SddParamsTest` (17 tests, each in both modes).
- `plugins/guardrails/skills/sdd-constitution/references/sdd-parameters.md` (new): each key, its values, its default
  and the step that reads it, marked KIT-068 or KIT-069 where that change wires it; the `rule_paths` example for a
  monorepo.
- `plugins/guardrails/skills/sdd-constitution/SKILL.md`: § 3 also writes the domain glossary (domain terms only, from
  the README and the code's folder and module names) and the architecture (base architecture with its decision, one
  row per area with rooted paths); § 4 sets the parameters, changing a key only on a fact or product choice, and reads
  `check_spec.py --params` back to product; § 5 writes `REVIEW.md` from the kit template, removing each line a project
  gate enforces and naming that gate under "Do not report"; § 7 also runs `sync-project.sh --check`.
- `plugins/guardrails/templates/spec-index.md`: the `sdd:` block at the kit defaults, a domain-only note on the
  glossary and an `## Architecture` section; `platforms/kits/sdd/init-spec.sh` copies it and notes a `spec.md`
  without the block.
- `platforms/kits/github/REVIEW.md`: each criterion ends with its skill section (`git` § 3, § 7; `review` § 2;
  `testing` § 2; `protocol-contract` § 2; `architecture` § 1, § 5; `security` § 2, § 4, § 5; `code-standards` § 9).
- `platforms/tools/sync-project.sh`: reads the block through `check_spec.py --params` before any write and refuses an
  invalid block or a `rule_paths` key that names no kit rule (exit 2, both modes); a `rule_paths` entry scopes that
  rule's globs and wins over the profile folders. `platforms/tools/sync_agents_md.py` (new) writes the rendered rules
  into a generated block in the `AGENTS.md` of each folder a rule's globs start in, appended to a hand-written file
  or in a new one, removed when no rule needs it; a folder that does not exist gets none, and a rule named after a
  profile the repository does not have (the map sends `java` to a godot repository) gets none. `--check` reports a
  missing, diverging or stale block. `test_sync_project.py` adds 7 tests.
- Text: `sdd-process.md` (the block), `README.md` (Codex row), `docs/projects.md`, `platforms/ci/README.md`,
  `platforms/tools/README.md`, `platforms/kits/sdd/README.md`, `platforms/kits/github/README.md`, `INDEX.md`.

[DECISION] The root `AGENTS.md` block also reaches Claude Code through the `CLAUDE.md` import, so a rule scoped to the
whole repository loads there at launch as well as by path: about 20 lines for the `json` rule in a `docs` project. A
`rule_paths` entry moves it to the folder that needs it.

A consumer resyncs (`sync-project.sh`) before writing the block: its old `spec.schema.json` refuses `sdd`. The resync
also writes the `AGENTS.md` blocks.

Follow-ups, outside this record: KIT-068 and KIT-069 wire their steps to the keys; no change in the approved split
wires `needs` and `journeys` into `sdd-intake`, `sdd-specify`, `sdd-clarify` and `sdd-check`; `pr_gates.py` keeps its
own `protected_paths` until `review` reads this one (KIT-069); KIT-070 moves the skill sections `REVIEW.md` cites; the
measurement that tells whether Codex reads the folder blocks (the falsifier: the godot and java counts above, after a
consumer's resync).

## Proof

`bash platforms/tools/check.sh` (also with `CI=1`), `bash platforms/tools/smoke.sh`,
`python3 platforms/ci/validations/check_kit.py --links`, the `test_check_spec`, `test_spec_trace` and `test_sync_project`
suites, and `gitleaks git --redact --log-opts=origin/main..HEAD`. Against `46c2602`'s `check_spec.py`, template and
`sync-project.sh`, 22 of the 24 new tests fail. The 2 that pass assert that a `spec.md` without the block passes and
that the sync creates no folder. Results are in the PR body.

## History

- 2026-11-14: confirmed (owner, chat): the split into KIT-066 to KIT-071 and their order ("aprovo"), and this change
  beside KIT-071 ("aprovo e pode começar em paralelo").
