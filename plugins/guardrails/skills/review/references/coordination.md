---
description: Coordination mode of skill review — one coordinator per delivery, blocker classes, green main per wave, conflict merges, batch review and evidence kinds.
kind: detail
---

# Coordination and batch review

For whoever merges a FEAT's or a batch's PRs (an orchestrator, an architect or the owner). The coordinator never reviews its own PR: each PR gets a delivery verdict from another context (`../SKILL.md`).

## One coordinator per delivery

- A delivery (a FEAT in feat mode, or a batch) has one coordinator. It owns the merge order, `main` staying green and the blocker log; workers and reviewers report to it.
- It keeps one notes file outside the repository for the delivery's state (rows, PRs, heads, verdicts, blockers), so a resumed or transferred session reads state instead of a transcript (skill `session`).

## Classify a blocker before working it

| Class | Meaning | Who acts |
|---|---|---|
| A — product defect | the code or the spec is wrong: a failing test, a red `main`, a contradiction | a fix row or `sdd-clarify` |
| B — missing evidence | the work may be right but nothing proves it: no record, a proof that cannot run, a capture not taken | the executor adds the evidence |
| C — process limitation | the tooling, a permission, the environment or a quota stops the work | the coordinator or the owner |

- Write the class next to the blocker before any attempt. At the second failure of the same class on one delivery, tell the owner with both attempts instead of a third.
- A blocked row is re-handed only after its spec is fixed or its question answered (skill `sdd-implement` § 3).

## Keep main green per wave

- After a wave's last merge, run the broad suite once on a clean checkout of `main` and record the command, commit and result.
- A red `main` stops every merge; a class-A fix row starts at once; merges resume when the suite passes on the fixed `main`.

## Merge with both sides

- Order merges by real `git merge-tree` conflicts. A conflict keeps both sides; check that the branch's net change survived by comparing `git diff <merge-base> <branch-head>` before the merge with `git diff <main> HEAD` after it. A conflict that needs a design choice aborts and goes to the architect.
- After the merge, the PR's verdict needs a re-check of the delta (step 9): an approval binds to the head it reviewed.

## Batch review

- After a wave or batch merges, one reviewer pass across its PRs together: duplicated helpers, names or constants that drifted between rows, decisions that contradict each other, and dead code (a function, branch, flag or parameter no caller reaches).
- Nits deferred from single-PR verdicts land here, once, as one fix row or a `DEBT-nnn`.

## Planned versus measured evidence

- Keep what was planned (an estimate, a target, an expected result) apart from what was measured (command output, with the command, commit and environment). Label each: `planned:` or `measured:`.
- A planned number never stands in as a result in a verdict, a closure record or a report; a measurement without its command is a claim.

## Owner-only approvals

- `owner_approvals` (`sdd:` parameter, default `[decision]`) lists change kinds only the owner approves; the coordinator never merges one on a reviewer's READY alone, even under owner-review autonomy.

Done when: every blocker carries its class and owner, `main` is green after each wave, every conflict merge kept both sides with the net-change check recorded, and the batch review's findings are rows, DEBTs or closed.
