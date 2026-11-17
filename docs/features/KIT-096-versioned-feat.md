---
id: KIT-096
title: "The versioned FEAT: one use case for the project's life, one block per project version"
status: in-progress
confirmed: "2026-11-16 (owner, kit chat: \"Sim, faça\" on E § 17, backlog G9; \"Yes, blocks\" on E § 17.1)"
issue: "#338"
pr: ""
---

# KIT-096 — The versioned FEAT: one use case for the project's life, one block per project version

## Problem and evidence

[FACT] The owner's game-profile evaluation (`KIT-GAME-PROFILE-EVALUATION-2026-11-16.md` in the owner's workspace,
"E" below) § 11.1: the kit says a FEAT is "never a bucket for later work", but nothing enforces it. `max_feat_tasks`
only warns, and nothing stops rows or REQs from joining a FEAT after `planned`. In Stratics (`origin/main`
`8d7495894`), 12 of 131 FEATs exceed 30 rows; FEAT-053 holds 248 rows and a 223-line History, open since 2026-10-07.
§ 13.1: 80 of the 657 REQs that FEATs list are listed by more than one FEAT, so one feature lives in several files.

The owner's decisions (E § 17.6): one versioned FEAT per feature (§ 13), the FEAT is a use case, one actor and one goal,
and one process holds N FEATs (§ 15); greybox and polish are two version blocks of one FEAT ("Yes, blocks", § 17.1).

## Change

- `feature.schema.json`: `processes`, items `PROC-nnn`, `PROC-nnn S<a>–S<b>`, `PROC-nnn S<n>` or `PROC-nnn A<n>`.
- `templates/spec-feature.md`: the FEAT is one use case (Scope opens with its actor and goal), `processes: []`, and
  `## Versions` replaces the top-level `## Tasks` and `## Closure`: one `### <version>` block per project version with
  `Status:`, a one-line `Scope:` (the REQs and ENB contracts the version adds or changes), `#### Plan delta`,
  `#### Tasks` and `#### Closure`. `## Plan` stays the use case's current design.
- `check_spec.py` (new functions `version_blocks`, `check_versions`, `check_block_rows`, `delivered_once`,
  `check_feature_processes`, `load_release`; three call sites): rule `version-block` (a block needs a valid `Status:`;
  every block but the last is delivered or cancelled; the FEAT's `status` is the last block's; every task row sits in a
  block; a block's Scope names only REQs the FEAT lists; unique block names; `## Versions` holds a block), rule
  `block-tasks` (an open block above `sdd.max_feat_tasks` rows fails; `MEASURED`, so `baseline.json` holds a block at
  its row count and a held block that grows fails), the chain, cycle and missing-row checks per open block (a
  `Depends on` an earlier block's row is satisfied), rule `feature-process` (`processes` names existing processes). A
  NEED delivered by an earlier block stays valid while the next block is open. A FEAT without `## Versions` takes the
  old path: the warning above `max_feat_tasks` is unchanged.
- `spec_trace.py` (new functions; one-line call sites in `load`, `derived_status`, `rewrite_status`, `closure_gaps`,
  `validate`, `deliver`, `apply_sync`, `check` and `main`): a versioned FEAT's status derives from its last block's rows
  only, and every writer keeps the block's `Status:` line equal to the frontmatter; `validate` reads the block's
  `#### Closure`; `check` checks the `processes` step ranges, each block name against the profile's
  `release.versioning` (KIT-088, read through `check_spec.load_release`, the resolver `load_params` uses) and the
  anti-bucket rule on each open block (a row cited by a process step outside the declared steps, a Scope REQ only such
  steps cite, an ENB the FEAT's `enablers` omits); new command `versions [--feat FEAT-nnn]` lists the blocks, the FEATs
  of each process (one process, N use cases) and the sdd-check C17 findings it reads from git: a REQ that joined a
  block's Scope after the block's first committed `planned` version, a row added after the block's first committed
  version with rows at `planned` or later, unless a History line names the row and a defect or a REQ of that Scope.
- Skills, body lines only: `sdd-plan` (one FEAT per use case, the next block instead of a second FEAT, `processes`,
  block `Status: planned`), `sdd-tasks` (rows in the open block, ids continue, additions after planned), `sdd-check`
  (row C17 and the `versions=` argument), `sdd-review` (the block's Closure), `sdd-release` (the block named by
  `release.versioning`); references `sdd-process.md`, `sdd-parameters.md`, `closure-record.md`; `platforms/ci/README.md`.

Choices:
- The rows live inside each block's table, so `task_table`, `sync-status`, `mark-done` and the row checks read them
  unchanged; row ids continue across blocks, so issue titles `[FEAT-nnn Tn]` stay unique.
- C17 reads git history instead of a hand-written snapshot line: `planned` is reached before `sdd-tasks` writes the
  rows, so the row snapshot is the block's first committed version with rows at `planned` or later, and the Scope
  snapshot its first committed `planned` version.
- `max_feat_tasks` fails only on versioned FEATs: no existing FEAT has `## Versions`, so no consumer breaks, and a
  FEAT converted to blocks with an oversized block is held by `baseline.json` (MINOR, not MAJOR).

## Proof

- Red first: `test_check_spec_versions.py` (24 tests) and `test_spec_trace_versions.py` (22 tests) failed 35 of 45
  before the change (the 10 that passed guard behavior that must not change); green after, under `python3.12` and
  `/usr/bin/python3` 3.9.
- Byte for byte: `check_spec.py` (full and `-S`), `spec_trace.py check`, `status`, `lint`, `enablers` and the rendered
  matrix on `platforms/ci/fixtures/consumer` and on a copy of Stratics' `docs/spec`, under both Pythons, before and
  after: 50 outputs, no difference (the clone-name list of the copy's sibling folders normalized).
- `bash platforms/tools/check.sh`, `bash platforms/tools/check.sh --links`,
  `python3.12 platforms/tools/run_tests.py --layer unit,contract`, `--layer integration --changed-from origin/main`.

## History

- 2026-11-16: confirmed (owner, E § 17, backlog G9).
- 2026-11-17: implemented on `feat/kit-096-versioned-feat`; PR pending. Stratics follow-up (not kit): split FEAT-053
  into use-case FEATs (E § 17.5 item 4).
