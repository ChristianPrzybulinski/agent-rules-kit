---
description: A field owned by another FEAT is fixed in that contract first.
tags: [ready]
max_turns: 10
allowed_tools: [Read, Glob, Grep]
---

/sdd-tasks FEAT-001

FEAT-001 has `status: planned`. Plan: the client sends the character's `facing` with every move. FEAT-002 owns the MoveRequest contract; its current contract has the fields `x`, `y` and `seq` and no `facing`. Produce the task table.
