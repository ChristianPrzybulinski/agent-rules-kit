---
name: sdd-implement
description: SDD step 6 — task-by-task Red-Green-Refactor delivery. Use when a FEAT has ordered tasks. Not for completion verdicts (skill validate-implementation).
argument-hint: "FEAT-nnn [T-nn]"
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

Process: `../sdd-constitution/references/sdd-process.md`.

## 1. Start one worktree per issue

`git worktree add ../<repo>-<N> -b feature/FEAT-nnn-Tn-<slug> main` — worktree commands: skill `parallelize`, its reference `worktrees.md`. Read the issue body as the spec and only the artifacts its `Spec` line names. Change only the paths in `Files`, plus a `changelog.d/` fragment when the repo uses one.

## 2. Execute each task

1. Mark `doing` and read every named file.
2. For behavior, run/write the test first; it must fail for the intended reason.
3. Implement the minimum, make the test green, then refactor.
4. Run the task's proof literally and summarize output in History.
5. Review conformance to task/criterion before code quality; a scope finding returns to implementation.
6. Commit atomically with Conventional Commits and `Refs: FEAT-nnn Tn`; `git status --porcelain` is empty before the PR; mark `done` when the PR merges.

A dependency/product/rule blocker becomes `blocked` with reason; never invent a workaround. Move only to an independent task.

## 3. Close the implementation

Use the `living-docs` reference in skill `update-docs`, update CHANGELOG/README/API docs and run full repository gates. Then call `validate-implementation`; PARTIAL/NOT READY returns to the missing task.

Incomplete work may merge only behind a recorded flag that defaults off. A flag continuously on for more than 30 days creates a `DEBT-nnn` removal item. Security/integrity rules never hide behind a flag.

## 4. Open one PR per issue

After the task's proofs and the DoD commands from `<repo>/AGENTS.md` § Commands pass, open a PR whose body has What, Why, How I tested (literal output), Proof (one allowlisted command per line) and the last line `Closes <owner>/<docs-repo>#N`. Never push to `main`, force-push, rebase or merge; the architect reviews the diff against FEAT/REQ/DEC and merges. Executor contract: `references/task-pr.md`.

Done when: the diff stayed inside `Files`, the proofs and DoD commands pass with literal output in the PR body, validation is READY, and incomplete merged behavior is safely flagged with expiry handling.
