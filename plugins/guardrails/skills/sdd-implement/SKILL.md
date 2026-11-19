---
name: sdd-implement
description: SDD step 6 — deliver a FEAT's tasks by Red-Green-Refactor, modes task, feat, fix. Use when a FEAT has ready rows or findings. Not for verdicts (skill review).
argument-hint: "FEAT-nnn [Tn | fix <PR>]"
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

# SDD 6 — Implement

Process: `../sdd-constitution/references/sdd-process.md`. Parameters: the project profile, resolved at § 1. It delivers rows; the verdict is always another context's (skill `review`). The path rules (`code.md`, `tests.md` and the stack's own) load with the files; each step below names the reference it reads.

## 1. Take the FEAT and the mode

Resolve the project profile first (`../session/references/project-profile.md`): `spec_root`, `sdd` (`pr_unit`, `commits_by`, `tracker`), `stacks`, `tests`, `quality` and `evidence` (`visual_approval`).

| Argument | Mode | Takes |
|---|---|---|
| `FEAT-nnn Tn` | task | that row, once ready |
| `FEAT-nnn` | feat | every ready row, wave by wave (§ 4) |
| `FEAT-nnn fix <PR>` | fix | only the PR's open findings, on its branch, by the executor that opened it, until each `close_when` holds |

- Read the FEAT once: Scope, acceptance criteria (CA), Plan, Tasks, Decisions, and the Verification of the REQs it lists.
- With a canonical FEAT `issue`, orient by each row's Status and its History/PR evidence, never by the shared issue's labels or closure. A row is ready when it is todo and every `Depends on` row is done. Legacy task issues and local TASK files (`tracker: none`, `docs/spec/tasks/`) remain their rows' state source until explicitly migrated; never prefer an old progress file.
- `pr_unit: task` opens one PR per row; `feat` one PR per FEAT, one commit series per row. Each PR unit gets its own worktree from `main`: `git worktree add ../<repo>-<slug> -b feature/FEAT-nnn-Tn-<slug> main` (`references/worktrees.md`).

## 2. Run the task cycle

1. Orient: the row's Files and Proof, the Plan § it points to, `<repo>/AGENTS.md`, `git log --oneline -20`. Record that row as doing with its execution reference; use the legacy item state only for an unmigrated task or local TASK file.
2. Red (`references/tdd.md`): write the test from the REQ's example or counterexample, or the row's CA, before the code. Run it and keep the failing line: it fails for the right reason (the missing behavior), not an import, typo or fixture error. Exceptions, named in the PR's `## Red`: a characterization test of existing behavior (`references/characterization.md`), or a manual proof with why no honest test exists.
3. Green: the smallest change on the YAGNI ladder (`references/coding.md` § 2), in the layer the Plan names; stack detail in `references/godot/README.md`, `references/java/README.md` or `references/assets.md`.
4. Refactor with the tests green; no behavior change.
5. Prove: run locally only the TDD loop (the row's Proof and the unit and integration tests covering the changed files) and the linters; CI runs the rest on the pushed head (`references/test-gates.md` § 3). Run a stack's recipe (`test`, `lint`, `boot`, `verify`) from the kit's just module for the folder's stack in the project profile, `just -f "$KIT/platforms/kits/just/<stack>.just" -d <folder> <recipe>`; the project keeps no justfile (`references/recipes.md`, KIT-085). A failure with no named cause goes to skill `investigate` before any fix.
6. Self-check: `references/task-pr.md` § Self-check.
7. Deliver: commit (`commits_by`), open the PR with `## Red`, the `proof` block and the executor line (`references/task-pr.md`), and record the row's PR on the FEAT issue; keep its Status doing until delivery is verified. A row PR uses `Refs`, never closes the shared FEAT issue.

- A test outside Files that reads a changed file may be widened under `## Files widened`: existing test paths only, each with its reason. An assertion changed to make a test pass is no widening: stop with `[BLOCKER]`.
- `commits_by: orchestrator`: the executor leaves the worktree uncommitted and the orchestrator commits. A round that cannot run the proof (no shell) says so on its `## Proof` line; the gates run it, and the PR is not READY before they do.
- In Claude Code (Claude-specific) the user may set `/goal <proof command> exits 0` before the row starts (code.claude.com/docs/en/goal, checked 2026-10-06); in every executor the Proof runs again on the pushed head where the project's gates run it (its CI or its loop's gate), else in review step 5, which re-runs each proof line no result is recorded for (`review_checks.py proof --run`).
- A PR that changes skills or rules (agent instructions the repository ships) runs their evals by hand before it opens, and its body cites the command and the score on an `Evals:` line. Evals bill a model and need its credential, so CI runs them only on demand and holds no such secret.
- A screen, UI, shader or motion change carries its capture in the PR (`--headless` renders nothing: capture from the editor or under `xvfb-run`) or follows the project's capture clause; `visual_approval` names who compares it with the REQ's mock before merge. A row of a greybox block under `sdd.passes` carries none: placeholder art has no mock, and the owner's playtest accepts it (`../sdd-review/references/playtest.md`).
- A secret the work creates is listed under `## Secrets to register` (name, where it lives, what it opens; never the value) for the owner's registry.

## 3. Handle a blocker

- The spec is ambiguous, contradicts a decision, or the Files cell cannot hold the change: stop, mark that row blocked with `[BLOCKER] <one line>` and its row id on the FEAT issue, and take an independent ready row. Never infer that all rows are blocked from the shared issue. The architect fixes the spec or answers, then re-hands the row; never invent a workaround.
- A planned red intermediate state (expand/contract, a failing test committed before its fix) lives only on the task branch, with the commit body naming the undo; `main` never receives it.
- Incomplete work merges only behind a recorded flag that defaults off; a flag on for more than 30 days creates a `DEBT-nnn` removal item. Security and integrity rules never hide behind a flag.

## 4. Run a wave in parallel

Feat mode runs the FEAT wave by wave: `references/parallel-waves.md` (wave 0 alone, one worktree per ready row, read-ahead workers while a row waits (`references/read-ahead.md`), the lead integrates and keeps `main` green per wave); whether two rows' shared files really conflict: `references/measure-conflicts.md`.

## 5. Close

- Each choice the spec did not fix gets one line in the FEAT's `## Decisions`: `YYYY-MM-DD T<n> (<PR>): chose X over Y because Z`; the action log stays in the PR body.
- Update CHANGELOG, README and API docs in the same PR (`references/living-docs.md`; a new dependency: `references/dependency-search.md`); a PR that changes a contract updates its ENB catalog row when the project keeps `docs/spec/enablers/`.
- Never push to `main`, force-push, rebase or merge your own PR. After each row merges with its proofs green, use `TRACE mark-done` with the row id and merged PR; record other row transitions with evidence in History. After the FEAT's last row merges, `sdd-review` closes the FEAT and its issue.

Done when: each row's test failed first (or `## Red` names the exception), each Proof and DoD command passes with literal output in its PR, every diff stays inside Files plus declared widenings, each row has its PR or blocker recorded with evidence, and incomplete merged behavior is flagged with expiry handling.
