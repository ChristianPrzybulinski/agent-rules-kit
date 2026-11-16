---
id: KIT-070
title: "The coding standards move from skills nobody loads into path rules and the references of the SDD step that uses them"
status: done
confirmed: "2026-11-14 (owner, chat of the SDD review session: \"Dev skills consolidation\" and item 1 of the six further adjustments, \"Aprovo todos\")"
issue: "#256"
pr: "#261"
---

# KIT-070 — The coding standards move from skills nobody loads into path rules and the references of the SDD step that uses them

## Problem and evidence

[FACT] In 30 days, 0 of 28 Claude Code sessions that edited `*.gd` or `*.java` loaded any of the nine coding-standard
skills, although each was listed with its description; Codex read `godot-standards` 18/18 and `testing` 23/23 by
description, but the godot path rule 0/18 and the java rule 3/6 (KIT-067 design record, 2026-11-14, issue #256).
Claude Code loads a path rule on a Read, Write or Edit of a matching file (official memory doc), and KIT-067 writes the
same rules into each folder's `AGENTS.md` block for Codex. Criterion approved by the owner: a skill exists only when
someone calls it on its own; everything else is a rule (loaded by path) or a reference of the SDD step that uses it.

[FACT] #240: the `parallelize` trigger case scored 0.00 over 5 runs (claude-sonnet-5-5, KIT-071) while Claude ran the
checks in parallel without the skill, and Codex loaded `parallelize` by description in 11 sessions over 60 days
(`skill_usage.py --days 60`, KIT-071 record).

## Change

| Skill | Goes to |
|---|---|
| `architecture` | `sdd-plan/references/architecture.md` + `pattern-catalog.md` |
| `code-standards` | rule `code.md` + `sdd-implement/references/coding.md`, `living-docs.md`, `dependency-search.md` |
| `godot-standards` | rule `godot.md` (23 body lines) + `sdd-plan/references/godot/` (design) and `sdd-implement/references/godot/` (coding), each with a `README.md` index |
| `java-standards` | rule `java.md` (20 body lines) + `sdd-implement/references/java/` with a `README.md` index |
| `testing` | rule `tests.md` + `sdd-implement/references/tdd.md`, `test-gates.md` (§ 3 the impact table), `characterization.md` |
| `persistence` | rule `migrations.md` + `sdd-plan/references/data.md`, `postgres-18.md`, `redis-7.md`; `investigate/references/database.md`; `sdd-release/references/backup.md` |
| `protocol-contract` | rule `protocol.md` (glob `**/protocol/**`, a project scopes it by `sdd.rule_paths`) + `sdd-plan/references/contract.md` § 0 |
| `asset-import` | rule `assets.md` + `sdd-implement/references/assets.md` |
| `security` | stays, 62 → 41 lines: release gates, incident, sensitive-change review; design rules go to `sdd-plan/references/security-design.md` |
| `grilling` | removed with its `skills.lock` line; its frontier idea goes to `sdd-clarify` § 2 |

- #239: skill `docker` (71 → 39 lines) keeps starting, diagnosing and deploying on a running or remote host; the
  file rules stay in `rules/docker.md` and the Twelve-Factor depth goes to `sdd-plan/references/twelve-factor.md`.
- #240: `parallelize` stays a slim model-invocable skill (description unchanged, Codex loads it); its fan-out,
  `worktrees.md` and `measure-conflicts.md` live in `sdd-implement`, the `AGENTS.md` line is a pointer, not a load
  trigger, and the `parallelize-trigger-three-checks` case is removed with its 0.00.
- #238: `hooks/hooks.json` gains an `InstructionsLoaded` hook that appends each rule or `CLAUDE.md` load
  (`file_path`, `load_reason`, `globs`, `trigger_file_path`, …) to `$CLAUDE_PLUGIN_DATA/instructions-loaded.jsonl`,
  rotated past 5 MiB, silent and fail-open; `skill_usage.py --rules` counts loads per rule from it and Codex reads of
  the rule files and the `sdd-*` references.
- `sync-profiles.txt` sends the new rules by profile and `sdd-plan`/`sdd-implement` to the code profiles;
  `sync_agents_md.py` says in the block where a vendored or installed kit skill lives, and each `.claude/rules/` copy
  carries the same under its marker (`.claude/skills/<skill>/references/<file>` when vendored, else
  `~/.ai-kit/plugins/guardrails/skills/<skill>/references/<file>`), since Claude cannot load the user-only `sdd-*`
  skills to find them. `sync-project.sh --check` fails on a consumer citation of a removed kit skill, backticks
  optional: `skill x`, `x skill`, `x § n`, `guardrails:x`, a `skills/x/` or `x/references/` path, `/x`, and a
  hyphenated name anywhere as a whole word; a plain word (`testing`, `architecture`) counts only in those forms. Same
  exclusions and `<!-- kit-path-ok -->` opt-out as its stale-path check; on the Stratics checkout (`d23561cba`) it
  flags 15 lines, `DGME-001-servidor-autoritativo.md:34` included. A scan that fails exits `--check` non-zero, and a
  line or file name the locale cannot encode prints escaped (review round 2).
- `check_kit.py` requires, at any depth, a `README.md` index for each nested reference folder that lists each of its
  files and is named in `SKILL.md` (one level deeper: in the parent index), checks every nested reference's
  frontmatter and 60-line limit, and runs the `InstructionsLoaded` hook on a sample load.
- Lines kept in their new homes (review of PR #261): "Fewer files win when cohesion remains high" in
  `sdd-implement/references/coding.md` § 4; "rejected simpler option understood, no speculative architecture" in the
  `architecture.md` Done line; read-only init mounts, the Java 25 JRE runtime and `.godot` in `.dockerignore` in rule
  `docker`; `REVIEW.md` points at the `security` § 3 checklist. Renumbered: `security` § 3-5 → `security-design.md`
  § 1-3 and § 6 → § 3; `docker` § 1-2 → rule `docker`, § 3-4 → § 1-2, § 5-9 → `twelve-factor.md` § 1-5.
- The `reviewer` agent preloads only `guardrails:review`; `AGENTS.md` (60 lines), `REVIEW.md`, the kit READMEs,
  `CONTRIBUTING.md`, `docs/design.md`, `smoke.sh` and the eval cases follow. Eval cases removed:
  `code-standards-one-decision-one-place`, `java-standards-no-field-injection`,
  `protocol-contract-required-field-bumps-version`, `parallelize-trigger-three-checks`, and, after the gate,
  `godot-standards-boot-exit-code` and the three `testing-*` cases.

## Gate: does Codex open the replacement?

Owner-approved condition for removing `godot-standards` and `testing`: Codex opens the replacement rule block or a
reference in 80% or more of runs; below that, a thin router skill stays.

Method: a monorepo fixture (`client/` Godot 4.7, `server/` Java 25) synced from this branch with
`sync-project.sh --vendor-skills --profile godot:client,java:server`, so `client/AGENTS.md` and `server/AGENTS.md`
carry the generated rule blocks and `.claude/skills/` holds `sdd-implement` and `sdd-plan`. Ten prompts that never
name a skill or a rule (five Godot edits or reviews, five test tasks), each run twice on a fresh copy with
`codex exec --json -s workspace-write --ephemeral --disable plugins` (Codex CLI 0.164.0), so no kit plugin skill is
listed. A run counts when one of its commands reads `client/AGENTS.md` or `server/AGENTS.md`, or a file under
`skills/sdd-implement/references/` or `skills/sdd-plan/references/`.

Result (2026-11-15, 20 runs, all exit 0): Godot 10 of 10 and testing 10 of 10 opened the rule block or a reference.
The block was read in 19 of 20 (the one other run, a flaky-test fix, read `sdd-implement/references/tdd.md`), and a
reference in 17 of 20: `characterization.md` in 6 of 10 test runs, `test-gates.md` in 2, a `godot/` reference in 7 of
10 Godot runs. So both skills are removed with no router.

Limitation: the machine's global `~/.codex/AGENTS.md` links to `~/.ai-kit` at `main`, which still cites skill
`testing` § 6, so 19 of 20 runs also opened that old `SKILL.md`; after the release and `refresh.sh` that line names
`sdd-implement` reference `test-gates.md` instead. A first batch without `--disable plugins` listed the cached old
skills and is not counted.

## Proof

Red on `origin/main` (`4f035d1`) with the new tests copied in: `test_check_kit_references` 2 failures, 2 errors
("a nested reference folder needs a README.md index" not found); `test_hooks_instructions_loaded` 8 failures,
3 errors ("one InstructionsLoaded hook", 0 != 1); `test_skill_usage` 3 errors (`RuleLoadsTest`);
`test_sync_project` 9 failures (the removed-skill citations pass `--check`; the block does not say where skills live).

On `681ace0`, 2026-11-15: `bash platforms/tools/check.sh` and `CI=1 bash platforms/tools/check.sh` exit 0 (`check: OK
(1 plugins, 18 skills, 11 rules, 13 templates, 14 readmes, 130 links, 57 hook cases, 13 shell scripts)`);
`check_kit.py --links` exit 0; `bash platforms/tools/smoke.sh` exit 0; `python3 -m unittest discover -s
platforms/ci/validations -p 'test_*.py'` ran 550 tests, OK (skipped=5); the touched suites ran 192 tests, OK;
`gitleaks git --redact --log-opts="origin/main..HEAD"` found no leaks; `review_checks.py red --base origin/main
--head HEAD` printed `red: OK — 21 of 29 failing tests are Red on base, and head passes`, and its 8 `runtime` flags
fail on base for the missing behavior (`--rules` unrecognized, no nested `godot/` folder, no `InstructionsLoaded`
hook).

Review round 1, on `e15eae4`: `check.sh` and `CI=1 check.sh` exit 0, `check_kit.py --links` exit 0, `smoke.sh` exit 0,
the full unit discovery ran 554 tests, OK (skipped=5), gitleaks found no leaks, and `review_checks.py red --base 00d8123
--head HEAD` printed `red: OK — 10 of 10 failing tests are Red on base, and head passes` (all assertions).

Review round 2, on `7b38a62`: `check.sh` and `CI=1 check.sh` exit 0, `check_kit.py --links` exit 0, `smoke.sh` exit 0,
the full unit discovery ran 560 tests, OK (skipped=6), gitleaks found no leaks, `shellcheck -S info` on
`sync-project.sh` exits 0, `review_checks.py red --base 91f5fe4 --head HEAD` printed `red: OK — 5 of 5 failing tests
are Red on base, and head passes`, and deleting each of the 8 form lines of the scan in a copy failed exactly its
subtest of `test_each_removed_skill_form_alone_fails`.

## History

- 2026-11-14: confirmed (owner, chat of the SDD review session).
- 2026-11-15: review of PR #261 at `00d8123` BLOCKED (coordinator); fix round on the same branch.
- 2026-11-15: delta review at `91f5fe4` BLOCKED on two items (coordinator); second fix round.
