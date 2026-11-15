---
name: sdd-review
description: "SDD step 8 — FEAT closure on main: criteria, REQ examples, REQ-NF, journeys, decisions. Use when a FEAT's last row merged. Not for PR verdicts (skill review)."
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

Process: `../sdd-constitution/references/sdd-process.md`. Runs once a FEAT's last task row merged, on a clean checkout of `main`, by a context that delivered none of its rows. It checks the FEAT as one delivery and moves it to `validated` (or `delivered` under `release: merge`). It edits only the FEAT's `## Closure`, Scope, criteria and conditionals, its status through the tool, and the follow-ups it files; a code fix goes back as a row.

Each step is `script` (a command whose output is read) or `judgment`. Every check is one row of the closure table, so a project can drop a row type that calibration shows never finds anything.

## 1. Gate the start (script)

`python3 <spec_trace.py> validate docs/spec FEAT-nnn --at <main sha> --check`, with the project's synced copy or `~/.ai-kit/platforms/ci/validations/spec_trace.py`. Before the closure record exists it must report only that record missing: every task row done (or superseded by another row), and every step of a journey that a NEED listing the FEAT names cites its tasks and tests (`Implemented by`, `Proven by`). A step still `—` goes back to `sdd-tasks` for the row that fills it.

## 2. Run the criteria on main (script, then judgment)

- Each technical criterion (CA-n): its test or command on `main`; record the command and the literal result.
- Each delivered REQ's Verification example and counterexample: the test that proves it on `main`, or its manual check by the named person.
- A proof that fails as written because a later PR moved or renamed its path is a stale proof, not a pass: find the current test (grep the CA or REQ id), run it, record both, and correct the cited path in the closure row.
- Each REQ-NF: metric, target, measurement — the command, environment and measured value. A planned value never stands in for a measured one (skill `review`, reference `coordination.md`).
- Each touched journey end to end: every step's `Proven by` test or manual check, in step order.
- The broad suite once on the same `main` commit (skill `testing` § 6, the broad row).

## 3. Reconcile decisions and conditionals (judgment)

- A settled `[DECISION]` line in the FEAT folds into Scope, a CA or a REQ (a REQ change goes through `sdd-clarify`), and the line keeps a marker: `→ folded into CA-3`.
- A conditional whose condition has since resolved ("until T19 lands", "once X is enabled") is rewritten as the current fact or deleted, citing the evidence (the merged PR, the config value).
- A FEAT is spec-first: after the closure it is frozen as history.

## 4. Decide the outcome

| Finding | Outcome |
|---|---|
| every row passes, nothing open | `validate … --at <sha>` (no `--check`): `validated`, or `delivered` with its NEED under `release: merge` |
| a defect in what the FEAT delivered | a new task row in this FEAT (`sdd-tasks` resync); the FEAT stays `in-progress` |
| a criterion or REQ that is ambiguous or wrong | `sdd-clarify` |
| broken behavior no artifact states | `sdd-intake` as a NEED of type `fix`, the failing check as Evidence |
| a gap the owner accepts for now | a task row in a later FEAT or a `DEBT-nnn` with its trigger |

A FEAT validates only when every closure row passes; an accepted gap is a row or a DEBT, never a silent pass.

## 5. Record the closure

Write the FEAT's `## Closure` before running `validate` without `--check`: the `main` commit, one row per check with its command and result, the folded decisions, the outcome and the retro numbers (blocked rows, review rounds, REQs amended after `planned`). Format and the commands that count: `references/closure-record.md`.

## Rules

- Never fix code here and never edit a REQ directly; never set `status` by hand: `spec_trace.py validate` writes it with its History line, which `check_spec.py` requires.
- A check that cannot run (no environment, no capture) is a closure row marked `not run: <why>`, and the FEAT does not validate on it.

Done when: every CA, REQ example and counterexample, REQ-NF and touched journey has a closure row with a literal result on one `main` commit, the decisions are folded, the retro numbers are recorded, and either `validate` moved the status or each finding has its follow-up item.
