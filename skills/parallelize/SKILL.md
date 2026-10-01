---
name: parallelize
version: "1.0"
description: Parallelizes independent work — batches independent tool calls in one turn, runs long commands in the background while work continues, fans out disjoint tasks to subagents when the platform offers them — and names what must stay sequential (depends on a result, shares a file/index/port/DB, has an external side effect). Use at the start of any task with more than one step, when a command will take more than a few seconds, when a task list has `[P]` tasks, or whenever you are about to issue calls one at a time that do not depend on each other. Do not use for concurrency inside the product's code (threads, async, locks — skills `java-standards`, `godot-standards`, `testing`).
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

Latency is paid once per **dependency**, not once per call. This skill turns a task into waves of independent work and names what must stay sequential; it does not decide *what* to do (that is the plan), only what leaves together. Parallel is not broader: run in parallel what you would run anyway — never add calls to fill slots.

## 1. Map dependencies before the first call

- List the steps. For each pair ask three questions: (a) does B need A's result? (b) do they share a resource — same file, git index/worktree, port, database, Maven/Gradle local repo, test fixture? (c) does either have an external side effect (push, deploy, e-mail, payment, state-changing API)? Three "no" → same wave.
- An edit and the check that verifies it are the same wave **only** if the platform executes calls in order; otherwise the check goes in the next turn.
- Steps whose result decides whether the next one is needed (a grep that may end the search) go first, alone — speculative reads behind them burn tokens.

## 2. Wave 1 — same turn (zero risk)

- Independent reads, greps, globs, status commands: all in one response. One read-only call when you already know the next three is a round trip wasted.
- Batching is not a substitute for the right call: one `wc -l` or `grep -c` over forty files beats forty parallel reads.
- A tool that cannot run in parallel (e.g. a search subagent) runs alone; the rest goes around it.
- Scope rule from `../tokens/SKILL.md` still holds: broad reading needs a hypothesis, parallel or not.

## 3. Wave 2 — background for long commands

- A command expected to take more than ~10 s (build, test suite, container start, download, dev server) starts in the background; work that does not depend on it continues (read the next file, write the next test); the output is collected when needed.
- Own the lifecycle: keep the handle/id; collect the output **before** claiming anything about the result; kill what you started (servers, watchers) or state explicitly that it stays up and why.
- Two background commands never share a resource: two Maven builds on one local repo, two servers on one port, two test runs on one database → sequential.

## 4. Wave 3 — fan out to subagents (when the platform has them)

- Candidates: `[P]` tasks from `../sdd-tasks/SKILL.md` with disjoint file sets; research in parallel with implementation; independent gates (lint ∥ tests ∥ build) when the environment tolerates it.
- Brief each with: goal, the exact files it may touch, the interface it must respect, how to verify, what to return. Two agents on one file is a merge conflict, not parallelism.
- The lead integrates and reviews every diff before it lands. A report is a claim; the diff and the command output are the evidence.
- Keep sequential: work whose output decides the next step (root-cause investigation), correctness-critical work (queries, metrics, security), anything with an external side effect.

## 5. Close

- Collect every background output before the summary — no "probably passed".
- Report per wave: what ran together, what was sequential and why (one line), what is still running.
- Done when: no step waited on an unrelated step; every started process is collected or explicitly left running; no shared-resource conflict happened.

## Rules — never in parallel

- Dependent steps; anything sharing a file, git index, port, database or lock; external side effects — one at a time, confirmed.
- Blind retry variants: "same error twice" demands a hypothesis, not five guesses at once.
- Git operations on one worktree (index lock). Two branches at once → `git worktree` (`references/worktrees.md`).
- Speculative reads to fill slots; widening the task to "use" the parallelism.
