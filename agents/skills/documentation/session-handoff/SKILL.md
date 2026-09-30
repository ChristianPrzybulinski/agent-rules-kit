---
name: session-handoff
version: "1.0"
description: Records the handoff between work sessions — what was done with evidence, what is pending, decisions made/open and the next session's first concrete task. Use when closing a long session, before switching agent/tool, or when context will be lost.
argument-hint: "[FEAT-xxx | session topic]"
triggers:
  - user
  - model
allowed-tools:
  - read
  - grep
  - glob
  - exec
---

# Session Handoff

A new session must be able to continue without this conversation. The record is short, factual and points to artifacts — it does not repeat content already in spec/DEC/commit.

## 1. Collect (not from memory)

- `git status --short` and `git log --oneline <base>..HEAD` in each touched repo: what was committed, what was left dirty.
- Specs with `status`/`updated` changed this session (`grep -l "updated: <today>" docs/spec -r`).
- Verification commands run and a summary of the literal output (OK / FAILED + excerpt).
- Questions asked to the user and the answers obtained.

## 2. Write

Template: `agents/templates/doc-session-handoff.md`. Destination in the project: `docs/sessions/YYYY-MM-DD-<topic>.md` (create the folder if missing; if the project defines another location in `AGENTS.md`, use it).

Each item classified: `[FACT]` (observed), `[DECISION]` (approved, with DEC), `[PROPOSAL]`, `[HYPOTHESIS]`, `[BLOCKER]`.

## 3. Next session's first task

Exactly one, executable without questions: a command or file + done criterion. If it depends on a user decision, the task is "obtain decision X" with the options listed.

## Rules

- Do not claim "tested"/"works" without command + output in the record.
- Do not copy long spec excerpts; link them.
- A dirty working tree is an explicit `[BLOCKER]`, with the files listed.
- The record goes in the same commit/PR that closes the session; if nothing was committed, the record is the only commit.
