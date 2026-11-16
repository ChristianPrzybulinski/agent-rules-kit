---
description: Running a FEAT's ready rows in parallel, wave by wave — worktrees, worker briefs, read-ahead, integration and green main. Load in feat mode.
kind: detail
---

# Parallel waves

Feat mode of skill `sdd-implement`. The waves come from the FEAT's `Wave` column (skill `sdd-tasks`, its reference `waves-and-models.md`); this reference runs them.

## Order

- Wave 0 runs alone and first: contracts, schemas, migrations and shared fixtures the later rows read. Its PRs merge before wave 1 starts.
- A later wave starts when every row it depends on is merged. Inside a wave, rows run together only when they share no file, index, port, database or fixture and neither has an external side effect. A shared file is no conflict until a `git merge-tree` replay says so (`measure-conflicts.md`); semantic hotspots (migration number, protocol version, error-code allocation) stay sequential.

## Fan out

- One worktree and branch per ready row (`pr_unit: task`), or per FEAT with one worker per row on disjoint paths (`pr_unit: feat`).
- Brief each worker in a fresh context, artifacts by path: goal, owned files and units, interface, the row's Red test, done criterion, the default for a missing detail, the proof command and a bounded report (paths changed, units covered, checks run, open items; no whole-task claim). Name the model tier: an omitted one inherits the lead's. Codex `spawn_agent` forks the whole thread unless `fork_turns="none"`.
- While a row waits for a slot or a dependency, read ahead: read-only prepare workers, one per area (code, tests, spec), write a context note the worker reads first and re-checks (`read-ahead.md`).

## Integrate

- The lead reviews every worker diff, compares covered units with assigned ones and does the gaps itself; a worker report is not evidence by itself.
- Merge in dependency order; a real `git merge-tree` conflict only orders the merges. A conflict merge keeps both sides, never one side's version of a file. Check that the branch's net change survived: save `git diff <merge-base> <branch-head>` before the merge, then compare it with `git diff <main> HEAD` after it; any difference outside the conflict is a defect. A conflict that needs a design choice aborts the merge and goes to the architect.
- Each row's PR still gets its own review (skill `review`); the lead never reviews its own integration.

## Keep main green per wave

- After a wave's last merge, run the broad suite once on a clean checkout of `main` (`test-gates.md` § 3, the broad row).
- A red `main` stops every merge. Create a fix row at once (blocker class A in skill `review`, reference `coordination.md`), deliver it in fix or task mode, and resume merges only when the broad suite is green again on the fixed `main`.
- Record the suite command, the `main` commit and the result in the wave's coordination note or the FEAT's History.

Done when: every row of the wave is merged or blocked with its reason, each worker diff was reviewed, and the broad suite passed on the `main` commit after the wave's last merge.
