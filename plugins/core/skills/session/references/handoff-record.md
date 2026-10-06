---
description: Handoff record procedure — collect observed state, name one continuation action and verify completeness.
kind: detail
---

# Handoff record

## Collect observed state

- Run `git status --short` and the relevant base-to-HEAD log/diff in every touched repository.
- Read changed specs/status/history, literal verification outputs and user decisions.
- Classify claims as fact, decision, proposal, hypothesis or blocker; never infer from memory.

## Name one continuation action

Give exactly one executable first task with a file/command and done criterion. If it needs a decision, the task is to obtain that decision with its options.

## Verify handoff completeness

Confirm each “tested/works” claim names its command and outcome, pending work has an owner/state, and the record is included in the same commit/PR that closes the session.
