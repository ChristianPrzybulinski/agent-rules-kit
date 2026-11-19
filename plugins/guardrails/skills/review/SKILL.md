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

Resolve the project profile first (`../session/references/project-profile.md`): `review`, `gates`, `evidence` and `quality`. A `record` step reads the result recorded for the exact pushed head (CI checks, or the project's gate record where it runs no CI on pull requests) and runs it once on a clean checkout only when none exists; a `script` step runs `RC <check>`, which reads the diff and git objects and runs no code; a `judgment` step is the reviewer's reading. Commands and detail: `references/delivery-steps.md`.

| # | Step | Kind | What it settles |
|---|---|---|---|
| 1 | Pin the criteria | judgment | criterion rows from the row's CA, its REQs' Verification, the Plan § it cites and the project `REVIEW.md`, written before reading the code; the author's verdict stays out |
| 2 | Gates | record | every required gate passes on the pushed head; a red or pending one is `NOT READY`; a record whose inputs are unchanged is reused on a `Reused:` line |
| 3 | Red check | record, then judgment | `red`'s result recorded for the head by CI or the project's gate record, else `red` run once on the clean checkout (the PR's `## Red` is the author's claim): Red is a test failing on base on an assertion or on a symbol the PR adds, head passing; a test-only PR is exempt; judge only what it flags, or the `## Red` exception |
| 4 | Scope | script | `scope`: paths inside Files, `## Files widened` only existing tests with no assertion changed, `protected_paths` labels |
| 5 | Acceptance | record, then judgment | `proof` lints the block (it needs a `proof` block and an `Executor:` line; the kit's own PRs, `project.kind: tooling`, carry neither, so skip it there: `delivery-steps.md`); a line with no result recorded for the head is re-run (`--run`); each CA the row covers has code, test and doc at `path:line` |
| 6 | Design | judgment | the diff follows the Plan § (layers, contract, data, flag); a deviation the Plan lacks is a `spec` finding; with `docs/spec/enablers/`, a contract change (endpoint, message, event, job, file layout, migration, content key, config) with no edit of its ENB catalog row is a `spec` finding |
| 7 | DoD | script, then judgment | `dod`: grep-able `REVIEW.md` lines and dropped assertions; then the lines no script checks |
| 8 | Verdict | judgment | § 4 |
| 9 | Re-check | judgment | after a blocker's fix (§ 4): a small delta with no new mechanism is the coordinator's to verify, with no new round; recorded results whose inputs are unchanged carry over |

## 2. Hold the evidence rules

- Judge the pushed head, never local state: its diff against the criteria and the results recorded for it (`references/delivery-steps.md` § Recorded results: reuse, the clean-checkout fallback, the security probe); reading with `grep` or `git show` is not a run.
- An author's or worker's report is a claim until a recorded result naming the commit backs it; a claim nothing backs is re-run once on a clean checkout, and one that the record or that run contradicts makes the verdict `NOT READY`.
- A proof must be able to fail: a gate that passes on empty input proves nothing. A dropped test count against the base, a deleted or skipped test or a loosened assertion the PR does not name is a weakened check (agent `reviewer` step 4).
- An approval binds to the head it reviewed, never to a later one; an acceptance no reviewer gave is never recorded.
- `evidence.visual_approval` (`owner` or `reviewer`) names who compares a screen or motion change's captures with its REQ's mock; with `owner`, the verdict waits for that approval. A row of a greybox version block under `sdd.passes` is exempt: placeholder art has no mock, and the owner's playtest line accepts it (skill `sdd-review`, reference `playtest.md`).
- A change of a kind listed in `owner_approvals` is never READY on the reviewer's word: the verdict names the kind and waits for the owner.

## 3. Pick the depth

Unknown impact takes the higher tier (skill `sdd-implement`, reference `test-gates.md` § 3).

| Tier (`test-gates.md` § 3 row) | Runs |
|---|---|
| light (row 1) | steps 1, 2 (doc, schema, link and generator checks), 4, 6, 7, 8 |
| standard (row 2) | every step |
| full (row 3) | every step, the broad suite's result recorded for the head (where pull-request CI runs a subset of the layers, a dispatched run of the full layers on that head), the `Security` DoD lines read in full, a targeted probe at each security boundary the diff touches; owner and security approvals stay |

## 4. Issue the verdict

Format and finding owners: `references/delivery-steps.md` § Verdict. `READY`: every criterion met, every required gate green, no blocker. `PARTIAL`: the gates are green and every criterion the PR claims is met, but the PR declares that it delivers part of its item and names the rest and its follow-up; a criterion missing without that declaration is blocker (a), so `NOT READY`. `NOT READY`: a blocker, a failing gate, or a target that cannot be validated.

One round per PR. A finding blocks only for one of four reasons, which it names:

- (a) an unmet acceptance criterion;
- (b) broken existing behavior: a failing test, a reproduced regression, or a weakened check the PR does not name (§ 2);
- (c) a security gap where untrusted input enters, or a secret or personal data exposed in code or logs;
- (d) a rule lost in a migration.

- Everything else (an edge case of a hygiene check, a nit, wording, a missing extra test) goes to one follow-up issue the verdict links, never to another round. Do not chase new spellings of an input a static check cannot fully model: simplify the check to a short documented rule, or run the thing in a real sandbox.
- A blocker has an owner (`spec`, `apply`, `judgment`) and a `close_when`. A fix delta that is small and adds no mechanism is verified by the coordinator (the red check plus a targeted probe), with no new round; a delta that adds a mechanism gets one round on the delta only.
- An ambiguous criterion is a spec gap; route it to `sdd-clarify` rather than guessing.
- `review.rounds` (profile parameter, default 3) is a ceiling, not a target: the bar above gives a PR one round plus one per fix delta that adds a mechanism, and a project that keeps more rounds sets its cap here. After that many rounds that end `NOT READY` on the same criterion, stop and hand the owner the criterion, each attempt and the failing excerpt.

Done when: every criterion has observed code, proof and documentation status, every step of the tier has its recorded result, script output or judgment, every blocker names its reason (a)–(d), the rest sits in one follow-up issue, and the verdict follows the rules above (other modes: the reference's own Done line).
