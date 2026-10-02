---
name: session-handoff
version: "1.1"
description: Session handoff record with evidence and next action. Use when switching agent/session or leaving pending work. Not for session summary (skill session-review).
argument-hint: "[FEAT-xxx | session topic]"
triggers:
  - user
allowed-tools:
  - read
  - grep
  - glob
  - exec
  - write
---

# Session Handoff

Use `../../templates/doc-session-handoff.md`; the record must let a new session continue without this conversation.

## 1. Collect observed state

- Run `git status --short` and the relevant base-to-HEAD log/diff in every touched repository.
- Read changed specs/status/history, literal verification outputs and user decisions.
- Classify claims as fact, decision, proposal, hypothesis or blocker; never infer from memory.

## 2. Write the record

Save to the project-defined location or `docs/sessions/YYYY-MM-DD-topic.md`. Link specs, decisions, commits and reports instead of copying them. A dirty tree lists every path and is an explicit blocker.

## 3. Name one continuation action

Give exactly one executable first task with a file/command and done criterion. If it needs a decision, the task is to obtain that decision with its options.

## 4. Verify handoff completeness

Confirm each “tested/works” claim names its command and outcome, pending work has an owner/state, and the record is included in the same commit/PR that closes the session.

Done when: repository state and evidence are reproducible, blockers/pending work are explicit and the next session has one unambiguous first action.
