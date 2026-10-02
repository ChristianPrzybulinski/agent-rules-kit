---
name: parallelize
version: "1.1"
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

## 1. Map dependencies

- List the steps. Two steps share a wave only when neither needs the other's result, they share no file/index/port/DB/fixture, and neither has an external side effect.
- Run a decision-producing step first and alone; do not launch work whose need depends on its result.
- An edit and its check stay sequential unless the platform guarantees ordered calls.

## 2. Batch immediate work

- Batch independent `read`, `grep`, `glob`, status and short `exec` calls in one response.
- Prefer one precise aggregate command over many file-by-file calls.
- Do not add speculative reads merely to fill a parallel wave; the scope rule in `../tokens/SKILL.md` still applies.

## 3. Background long work

- Start commands expected to exceed 10 seconds in the background while unrelated work continues.
- Keep the process handle, collect literal output before reporting, and stop servers/watchers when finished.
- Do not run concurrent commands that contend for one local repository, port, database or test fixture.

## 4. Fan out disjoint tasks

- Fan out `[P]` tasks from `../sdd-tasks/SKILL.md` only when file ownership is disjoint.
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
