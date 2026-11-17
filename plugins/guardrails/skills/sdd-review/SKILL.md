---
name: sdd-review
description: "SDD step 8 — FEAT closure on main: task proofs, stale-text and trace lint, REQ-NF. Use when a FEAT's last row merged. Not for PR verdicts (skill review)."
argument-hint: "FEAT-nnn"
triggers:
  - user
disable-model-invocation: true
allowed-tools:
  - read
  - glob
  - grep
  - edit
  - exec
---

# SDD 8 — Review the FEAT on main

Process: `../sdd-constitution/references/sdd-process.md`. Runs once a FEAT's last task row merged, on a clean checkout of `main`, by a context that delivered none of its rows. It checks the FEAT as one delivery and moves it to `validated` (or `delivered` under `release: merge`). It edits only the FEAT's `## Closure`, Scope, criteria, stale text and proof paths, its status through the tool, and the follow-ups it files; a code fix goes back as a row.

Scripts do the mechanical part; the model reads only what they flag. Resolve the project profile first (`../session/references/project-profile.md`): `spec_root` (every `docs/spec` here), `sdd`, `review`, `gates` and `evidence`; `TRACE` and `RC` are its § 3 commands. Calibration (`references/closure-record.md` § Calibration): on 5 delivered FEATs every finding was a rotted proof, stale text or an untested clause, and 0 of 3,263 tests failed.

## 1. Gate the start (script)

`python3 TRACE validate docs/spec FEAT-nnn --at <main sha> --check`. Before the closure record exists it must report only that record missing: every task row done (or superseded by another row, or cancelled by a resync), and every step of a journey that a NEED listing the FEAT names cites its tasks and tests, and so does every step of a process that NEED names in `processes` or that such a journey cites (a citing journey step is filled when the process steps it expands to are). A step still `—` goes back to `sdd-tasks` for the row that fills it.

## 2. Run the scripts on main

- Task proofs: `RC feat-proofs --feat docs/spec/features/FEAT-nnn*.md --run --gates <gates.json> --cwd <folder>` (`--rows` per folder). Each command runs literally after its paths are checked; a run whose output matches its stack's failure pattern fails even at exit 0 (a Godot `-s` run that prints `Can't load script`, `SCRIPT ERROR` or `Parse Error`); a stack lint flags a command that cannot prove what it names (Maven `-Dtest` with `verify` runs every IT). The project adds patterns with `--patterns`.
- Stale text and trace: `python3 TRACE lint docs/spec FEAT-nnn` — "Not verified" or an Audit still "Pending", `[PROPOSAL]` in Scope, `[HYPOTHESIS]` in Open questions or a done row, "until/once Tn" whose Tn is done, a Plan row count that differs from the table, a History bullet split by lines inserted inside it, and each listed REQ's proving test missing from its trace row.
- Broad suite: reuse the record of the last wave's broad suite on `main` ("main green per wave", skill `review`, reference `coordination.md`) when `main` has not moved under the FEAT's files since; otherwise run it once. There is no separate re-run of each REQ's tests.

## 3. Judge what the scripts flagged

- A stale proof (a path that moved, a renamed id): find the current test (grep the CA or REQ id), run it, record both, and correct the Proof cell. Re-run only the proofs this changed.
- A stale marker: rewrite it as the current fact or delete it, citing the evidence (the merged PR, the config value). A flagged `[PROPOSAL]` in Scope that is settled folds into Scope as fact, a CA or a REQ (a REQ change goes through `sdd-clarify`), keeping the profile's `decision_folding.marker`: `→ folded into CA-3` (`sdd-plan` § 5). A split History bullet: move the inserted lines below the bullet's last line.
- A trace gap: link the test in the journey or process step's `Proven by` (for a journey step that cites a process, in the cited process step), or correct the REQ's proving test.
- Each REQ example and counterexample against an asserting test (`path:line`): the output is a list of missing-test rows, not a block on `validated`. The reading is fallible (1 of 3 spot checks was wrong in calibration), so grep each "untested" claim before filing its row.
- Each REQ-NF: metric, target, measurement — the command, environment and measured value. A planned value never stands in for a measured one.
- A touched journey's or process's `manual:` checks, by the person each names; the automated `Proven by` tests are in the broad suite.

## 4. Decide the outcome

| Finding | Outcome |
|---|---|
| every script passes after the fixes above, nothing open | `validate … --at <sha>` (no `--check`): `validated`, or `delivered` with its NEED under `release: merge` |
| a defect in what the FEAT delivered | a new task row in this FEAT (`sdd-tasks` resync); the FEAT stays `in-progress` |
| a missing test for a REQ clause | a task row in this or a later FEAT; does not block `validated` |
| a criterion or REQ that is ambiguous or wrong | `sdd-clarify` |
| broken behavior no artifact states | `sdd-intake` as a NEED of type `fix`, the failing check as Evidence |
| a gap the owner accepts for now | a `DEBT-nnn` with its trigger |

## 5. Record the closure

Write the FEAT's `## Closure` (in a FEAT with `## Versions`, the open block's `#### Closure`; `validate` then moves the block's `Status:` line with the frontmatter) before running `validate` without `--check`: the `main` commit, one row per script and judgment with its command and result, the fixes made, the missing-test rows filed, the outcome and the retro numbers (blocked rows, review rounds, REQs amended after `planned`). Format and counts: `references/closure-record.md`.

With `docs/spec/enablers/`, the record adds an Enablers row: `TRACE enablers docs/spec --feat FEAT-nnn` and `TRACE check docs/spec` on that commit. A `high` finding, or any finding on this FEAT's ENBs or contracts, blocks the closure (a gap goes back as a row or to `sdd-plan`); a `medium` finding on another ENB is reported in the row and does not block, as in `sdd-check` § 3, although the tool exits 1 on it. After `validate` moves the status, run `TRACE generate docs/spec` and commit `traceability.md` with the closure: § Enablers is each ENB's generated History, which then lists the FEAT with its new status; never write it into the ENB file.

## Rules

- Never fix code here and never edit a REQ directly; never set `status` by hand: `TRACE validate` writes it with its History line, which `check_spec.py` requires.
- A check that cannot run (no environment, no capture) is a closure row marked `not run: <why>`, and the FEAT does not validate on it.

Done when: the task proofs, the lint and the broad-suite record are green on one `main` commit (stale ones corrected), each flagged item is fixed or filed, each REQ-NF is measured, the retro numbers are recorded, and either `validate` moved the status or each finding has its follow-up item.
