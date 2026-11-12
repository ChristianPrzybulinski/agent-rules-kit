---
name: parallelize
description: Parallel planning for tool calls, long commands and [P] tasks. Use when work has independent steps. Not for product concurrency (skill testing).
argument-hint: "[task or step list | empty]"
triggers:
  - user
  - model
allowed-tools:
  - read
  - grep
  - glob
  - exec
---

# Parallelize

Surfaces: local Devin uses subagents (`researcher` read-only, `reviewer` gates/review, or built-in `subagent_explore`/`subagent_general`); Devin Cloud uses managed Devins within ACU limits because profiles and hooks do not load there; Codex has no subagents, so keep steps sequential or ask the user to open parallel sessions.

## 1. Map dependencies

- List the steps. Two steps share a wave only when neither needs the other's result, they share no file/index/port/DB/fixture, and neither has an external side effect.
- Run a decision-producing step first and alone; do not launch work whose need depends on its result.
- An edit and its check stay sequential unless the platform guarantees ordered calls.

## 2. Batch immediate work

- Batch independent `read`, `grep`, `glob`, status and short `exec` calls in one response.
- Prefer one precise aggregate command over many file-by-file calls.
- Read only the material the outcome needs; broad reading needs a named hypothesis, and no speculative read is added merely to fill a parallel wave.
- Bulk output (long logs, wide searches, full test runs) goes to a subagent or a file; the main thread keeps the summary and the path.

## 3. Background long work

- Start commands expected to exceed 10 seconds in the background while unrelated work continues.
- Keep the process handle, collect literal output before reporting, and stop servers/watchers when finished.
- Before waiting on `pgrep -f <pattern>`, list its matches once (`pgrep -fl`): the pattern also matches leftovers of earlier runs and any other shell or wrapper holding it. Narrow it to the processes meant, bracket one character (`'[l]oop.py gates'`) so the waiting shell stays out of other counts, and give the wait a deadline.
- Do not run concurrent commands that contend for one local repository, port, database or test fixture.

## 4. Fan out disjoint tasks

- Fan out `[P]` tasks from skill `sdd-tasks` when they have no real conflict. Without evidence, disjoint file ownership is the test; a shared file is no conflict until a `git merge-tree` replay says so (`references/measure-conflicts.md`). Keep real dependencies and semantic hotspots (migration number, protocol version, error-code allocation) sequential.
- While a task waits for a slot or a dependency, read ahead: read-only prepare workers, one per area (code, tests, spec), write a context note that the implementer reads first and re-checks (`references/read-ahead.md`).
- Brief each worker with its goal, owned files, interface, verification command and required report.
- The lead reviews every diff and integrates results; a worker report is not evidence by itself.

## 5. Keep unsafe work sequential

- Keep dependencies, shared resources, correctness-critical queries, and external effects sequential.
- Serialize Git operations on one worktree; use another worktree when branches must progress independently (`references/worktrees.md`).
- After the same failure twice, stop parallel retries and form a new hypothesis.

## 6. Close

- Collect every background result and name anything intentionally left running.
- Report what ran together, what stayed sequential and why.

Done when: no unrelated step waited unnecessarily, no shared resource raced, and every started process has a collected result or an explicit owner.
