---
name: parallelize
description: Parallel tool calls, background commands, safe ordering. Use when a session has independent steps or long commands. Not for task waves (skill sdd-implement).
argument-hint: "[step list | empty]"
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

Runs one session's independent steps together and keeps unsafe ones in order. A FEAT's rows in waves, with worktrees, workers, read-ahead and conflict measurement, are skill `sdd-implement` (references `parallel-waves.md`, `worktrees.md`, `measure-conflicts.md`). Surfaces: local Devin uses subagents (`researcher` read-only, `reviewer` gates/review, or built-in `subagent_explore`/`subagent_general`); Devin Cloud uses managed Devins within ACU limits because profiles and hooks do not load there; Codex `spawn_agent` forks the whole thread, model included, unless `fork_turns="none"`: pass it with a self-contained brief.

## 1. Map dependencies

- List the steps. Two steps share a wave only when neither needs the other's result, they share no file/index/port/DB/fixture, and neither has an external side effect.
- Run a decision-producing step first and alone; do not launch work whose need depends on its result.
- An edit and its check stay sequential unless the platform guarantees ordered calls.

## 2. Batch immediate work

- Batch independent `read`, `grep`, `glob`, status and short `exec` calls in one response.
- Prefer one precise aggregate command over many file-by-file calls.
- Read only the material the outcome needs; broad reading needs a named hypothesis, and no speculative read is added merely to fill a parallel wave.
- Bulk output (long logs, wide searches, full test runs) goes to a subagent or a file; the main thread keeps the summary and the path. Filter at the source (a script, `jq`, `grep`, a line range) so only the answer prints; redirect before slicing (`cmd > out.txt 2>&1`), since a pipe into `tail` reports tail's exit status.

## 3. Background long work

- Start commands expected to exceed 10 seconds in the background while unrelated work continues.
- Keep the process handle, collect literal output before reporting, and stop servers/watchers when finished.
- Before waiting on `pgrep -f <pattern>`, list its matches once (`pgrep -fl`): the pattern also matches leftovers of earlier runs and any other shell or wrapper holding it. Narrow it to the processes meant, bracket one character (`'[l]oop.py gates'`) so the waiting shell stays out of other counts, and give the wait a deadline.
- A recurring or unattended job (loop, cron, scheduled task) names the skill it runs instead of copying its steps, states its stop condition and who acts on its output, and stops with a report at an ask-first action.

## 4. Keep unsafe work sequential

- Serialize Git operations on one worktree; use another worktree when branches must progress independently (skill `sdd-implement`, reference `worktrees.md`).
- A subagent gets a self-contained brief (goal, paths, done criterion, a bounded report) and a named model tier; its report is a claim the caller checks. Whether two branches' shared files really conflict: skill `sdd-implement`, reference `measure-conflicts.md`.

## 5. Close

- Collect every background result, on later turns too (a job with no result is checked, not assumed done), and name anything intentionally left running.
- Report what ran together, what stayed sequential and why.

Done when: no unrelated step waited unnecessarily, no shared resource raced, and every started process has a collected result or an explicit owner.
