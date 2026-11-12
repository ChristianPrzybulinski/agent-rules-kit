---
name: sdd-implement
description: SDD step 6 — task-by-task Red-Green-Refactor delivery. Use when a FEAT has ordered tasks. Not for completion verdicts (skill review).
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

Orient: read `docs/spec/progress/FEAT-nnn.json` and `git log --oneline -20`; pick the first task with `passes: false` whose `Depends on` cell in the FEAT task table names only tasks (by `Tn` or by `issue` number; the issue-per-task flow writes `FEAT-nnn Tn` or `#N`) that already have `passes: true`; never trust a Markdown `Status` cell over the file.

1. Mark `doing` and read every named file.
2. For behavior, run/write the test first; it must fail for the intended reason.
3. Implement the minimum, make the test green, then refactor.
4. Run the task's proof literally and summarize output in History. When the task closes, write one line in the FEAT's `## Decisions` for each choice the spec did not fix: `YYYY-MM-DD T<n> (<PR>): chose X over Y because Z`; decisions only, the action log stays in the PR body.
5. Gate on the proof before moving on. In Claude Code (Claude-specific) the user sets `/goal <proof command> exits 0` before the task starts (the agent cannot invoke the built-in command itself); the goal evaluator re-checks the transcript after every turn until the proof output shows exit 0, so paste the literal proof output (syntax: code.claude.com/docs/en/goal, checked 2026-10-06). In Devin or any other executor, the Proof section of the PR body (§4) is the gate: the reviewer re-runs every line on a clean checkout and a failing line blocks. Set `passes: true` in the progress file only after the proof's literal output is recorded; on failure keep `false` and put the first failing line in `notes`. Commit the file in the task's commit (checkpoint). For a visual change (scene, UI, shader, animation) the PR carries a screenshot or GIF; `--headless` renders nothing, so capture from the editor or run the capture under `xvfb-run` in CI (verify against the Godot command-line docs before relying on it).
6. Review conformance to task/criterion before code quality; a scope finding returns to implementation.
7. Commit atomically with Conventional Commits and `Refs: FEAT-nnn Tn`; `git status --porcelain` is empty before the PR; mark `done` when the PR merges.

A dependency/product/rule blocker becomes `blocked` with reason; never invent a workaround. Move only to an independent task.

A planned red intermediate state (expand/contract, a failing test committed before its fix) is allowed only inside the task branch, with the commit body naming the undo; `main` never receives it.

## 3. Close the implementation

Use the `living-docs` reference in skill `code-standards`, update CHANGELOG/README/API docs and run full repository gates. Then call `review`; PARTIAL/NOT READY returns to the missing task.

Incomplete work may merge only behind a recorded flag that defaults off. A flag continuously on for more than 30 days creates a `DEBT-nnn` removal item. Security/integrity rules never hide behind a flag.

## 4. Open one PR per issue

After the task's proofs and the DoD commands from `<repo>/AGENTS.md` § Commands pass, open a PR whose body has What, Why, How I tested (literal output), Proof (one allowlisted command per line) and the last line `Closes <owner>/<docs-repo>#N`. Never push to `main`, force-push, rebase or merge; the architect reviews the diff against FEAT/REQ/DEC and merges. Executor contract: `references/task-pr.md`.

Done when: each proof gated, every task in the progress file has passes: true, the diff stayed inside `Files`, the proofs and DoD commands pass with literal output in the PR body, validation is READY, and incomplete merged behavior is safely flagged with expiry handling.
