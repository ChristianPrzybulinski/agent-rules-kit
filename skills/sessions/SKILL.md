---
name: sessions
version: "1.0"
description: Session hygiene — plan before executing, one session = one outcome, detect context mixing and long sessions, suggest a smaller model tier for simple tasks. Use at the start of every session and when the request changes topic. Do not use for writing the handoff record (skill session-handoff).
triggers:
  - user
  - model
allowed-tools:
  - read
  - grep
  - glob
---

# Sessions

A short, focused session costs fewer tokens and errs less. These rules exist so the agent **proposes** the discipline, not to lock the user in: they decide.

## Start

- Read the repo's `AGENTS.md`; identify **the** outcome of this session in one sentence. Couldn't? Ask before any broad reading.

## Plan before executing

- Task with 3+ files, crosses a layer, or ambiguous request → if the session is **not** in planning mode, suggest the switch in one line ("this calls for a plan; switch to plan mode?") before touching a file. 1-2 file mechanical task → execute directly.
- Approved plan → execute without re-planning at every step.

## One session, one outcome

- One outcome = one FEAT, one bug, one decision, one document. A request from another context mid-session → **warn and stop**: "this is another topic; do I log it as a follow-up and we continue the current one, or do we close and open a new session?" Never mix silently.
- Follow-ups go to the handoff record (`session-handoff`), not to the agent's memory.

## Long session

Signals: rereading files already read, summarized/compressed context, original outcome already delivered with new requests arriving, more than ~2h of work. On noticing a signal → suggest: `session-handoff` + new session. Continue only if the user says so.

## Agent tier

- Simple task (mechanical, 1-2 files, no decision, no investigation) → say in one line that a smaller model/tier handles it, and proceed with the current one if the user doesn't switch.
- Task with architecture decision, investigation or risk → do not suggest downgrading.

## End

- `session-review`: summary + review of the session against the kit (proposal only with evidence; the user decides).
- `session-handoff` if the session produced something or left something pending.
- Working tree clean or listed as `[BLOCKER]`.
