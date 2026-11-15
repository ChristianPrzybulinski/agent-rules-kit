---
name: review
description: Completion verdict, claim check and PR gates. Use when asking “is it done?”, preparing a PR or testing a claim. Not for fixing failures (skill sdd-implement).
argument-hint: "[FEAT-nnn Tn | PR <n> | spec path | request | claim | --pr <n> | --batch <PRs>]"
triggers:
  - user
  - model
agent: reviewer
context: fork
background: false
allowed-tools:
  - read
  - grep
  - glob
  - exec
---

# Review

Verifies a delivery someone else made and reports a verdict with sources. It never fixes, commits or pushes: an `apply` finding carries its exact patch and the fix round (skill `sdd-implement`, mode fix) applies it, on docs PRs too. Bugs with no named cause go to skill `investigate`; a FEAT's closure on `main` is skill `sdd-review`.

| Argument | Mode | Procedure |
|---|---|---|
| a task row, PR, FEAT, spec path or request (default) | delivery verdict | §1–§4 |
| one claim or proposed solution | claim check | `references/claim-check.md` |
| `--pr <n>` with a gates config | no-model PR gates | `references/pr-gates.md` |
| `--batch <PRs>`, a wave, a merge conflict, a red `main` or a blocker | coordination and batch review | `references/coordination.md` |

## 1. Run the steps in order

A `script` step runs `python3 ~/.ai-kit/platforms/tools/review_checks.py <check>` (or a project gate) and the reviewer reads its output; a `judgment` step is the reviewer's reading. Commands and detail: `references/delivery-steps.md`.

| # | Step | Kind | What it settles |
|---|---|---|---|
| 1 | Pin the criteria | judgment | criterion rows from the row's CA, its REQs' Verification, the Plan § it cites and the project `REVIEW.md`, written before reading the code; the author's verdict stays out |
| 2 | Gates | script | the depth tier's gates on a clean checkout of the pushed head; a record whose inputs are unchanged is reused on a `Reused:` line |
| 3 | Red check | script, then judgment | `red`: Red is a test failing on base on an assertion or on a symbol the PR adds, head passing; a test-only PR is exempt; judge only what it flags, or the `## Red` exception |
| 4 | Scope | script | `scope`: paths inside Files, `## Files widened` only existing tests with no assertion changed, `protected_paths` labels |
| 5 | Acceptance | script, then judgment | `proof --run` re-runs the proof block; each CA the row covers has code, test and doc at `path:line` |
| 6 | Design | judgment | the diff follows the Plan § (layers, contract, data, flag); a deviation the Plan lacks is a `spec` finding |
| 7 | DoD | script, then judgment | `dod`: grep-able `REVIEW.md` lines and dropped assertions; then the lines no script checks |
| 8 | Verdict | judgment | § 4 |
| 9 | Re-check | script, then judgment | after a fix round, only the delta and the assumptions it touches; recorded results whose inputs are unchanged carry over |

## 2. Hold the evidence rules

- Validate the pushed head on a clean checkout; local uncommitted state never counts. An author's or worker's report is a claim until a command or a record naming the commit backs it; a claimed result that fails there makes the verdict `NOT READY`.
- A proof must be able to fail: a gate that passes on empty input proves nothing. A dropped test count against the base, a deleted or skipped test or a loosened assertion the PR does not name is a weakened check (agent `reviewer` step 4).
- An approval binds to the head it reviewed, never to a later one; an acceptance no reviewer gave is never recorded.
- `visual_approval` (`owner` or `reviewer`) names who compares a screen or motion change's captures with its REQ's mock; with `owner`, the verdict waits for that approval.
- A change of a kind listed in `owner_approvals` is never READY on the reviewer's word: the verdict names the kind and waits for the owner.

## 3. Pick the depth

Unknown impact takes the higher tier (skill `testing` § 6).

| Tier | Impact row | Runs |
|---|---|---|
| light | docs only | steps 1, 2 (doc, schema, link and generator checks), 4, 6, 7, 8 |
| standard | bounded code | every step; proofs without a record re-run |
| full | shared integration, authorization, persistence or migration | every step, the broad suite, every proof re-run, the `Security` DoD lines read in full; owner and security approvals stay |

## 4. Issue the verdict

Format, severities and finding owners: `references/delivery-steps.md` § Verdict. `READY`: every criterion met, every gate passes. `PARTIAL`: a criterion missing or partial while gates run. `NOT READY`: a gate fails or the target cannot be validated.

- Each finding has a severity (blocker, should-fix, nit), an owner (`spec`, `apply`, `judgment`) and a `close_when` the next round checks. Architecture, security and weak-test findings are blockers in the PR; a style nit may go to the batch review.
- An ambiguous criterion is a spec gap; route it to `sdd-clarify` rather than guessing.
- After `review_rounds` (`sdd:` parameter, default 3) rounds that end `NOT READY` on the same criterion, stop: hand the owner the criterion, each attempt and the failing excerpt.

Done when: every criterion has observed code, proof and documentation status, every step of the tier has its script output or judgment, all gates have literal results, and the verdict follows the rules above (other modes: the reference's own Done line).
