---
description: Handoff record procedure — collect observed state, name one continuation action and verify completeness.
kind: detail
---

# Handoff record

## Collect observed state

- Run `git status --short` and the relevant base-to-HEAD log/diff in every touched repository.
- Read changed specs/status/history, literal verification outputs and user decisions.
- For a FEAT in implementation with canonical `issue`, read its row Status and History/PR evidence, never derive every row from the shared issue. For legacy FEATs, read task issues (`tracker: github`) or the `TASK-nnn` files' `status` (`tracker: none`, `docs/spec/tasks/`); the record names the rows not yet done. A FEAT cut before KIT-068 may still keep `docs/spec/progress/FEAT-nnn.json`, which is read only as history.
- Classify claims as fact, decision, proposal, hypothesis or blocker, each with the date and commit it held at; never infer from memory.
- Under Decisions, record each approach tried and dropped with the evidence that dropped it, so the next session does not retry it.
- For a device or host that another session also uses (disk, USB bridge, VM, port), name the owner session of each device and the commands no other session may run on it (SMART, partitioning, authorize or unbind) before the first probe. A peer message that got no reply is not a release.

## Name one continuation action

Give exactly one executable first task with a file/command, the skills to load by name and a done criterion. If it needs a decision, the task is to obtain that decision with its options.

## Verify handoff completeness

Confirm each “tested/works” claim names its command and outcome, pending work has an owner/state, and the record is included in the same commit/PR that closes the session.
