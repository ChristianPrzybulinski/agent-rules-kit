---
name: sessions
version: "1.1"
description: Session scope and hygiene. Use when starting, changing topics or detecting a long session. Not for recording completed work (skill session-handoff).
triggers:
  - user
  - model
allowed-tools:
  - read
---

# Sessions

## 1. Start with one outcome

- Read the repository's `AGENTS.md` and README before broad exploration.
- Name one outcome for the session in a single sentence. If it cannot be named, ask before proceeding.

## 2. Plan at the right threshold

- For work spanning three or more files, crossing a layer, or containing ambiguity, propose planning mode before editing.
- For a one- or two-file mechanical change, proceed directly.
- Once a plan is approved, execute it without repeatedly reopening the plan.

## 3. Protect the scope

- A new topic mid-session is not silently added. Ask whether to record it as a follow-up or close and start another session.
- Keep follow-ups in the handoff record, not conversational memory.

## 4. Detect an exhausted session

Signals include rereading already-read files, compressed context, an outcome already delivered, new unrelated requests, or roughly two hours of work. Suggest `session-handoff` and a new session; continue only if the user chooses to.

## 5. Match the agent tier

- Suggest a smaller tier for a mechanical one- or two-file task with no decision or investigation.
- Keep the current tier for architecture, investigation or risk.

## 6. Close explicitly

- Invoke `session-review` for the evidence summary and optional kit proposal.
- Invoke `session-handoff` when work is committed, pending or transferring to another agent.
- Leave the tree clean or list the dirty paths as a blocker.

Done when: one outcome stayed in scope and the session ends with verified status, unverified items and one next step.
