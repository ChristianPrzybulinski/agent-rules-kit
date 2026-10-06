---
description: Every task that adds code lists a test path in its Files cell.
tags: [ready]
max_turns: 10
allowed_tools: [Read, Glob, Grep]
---

/sdd-tasks FEAT-001

FEAT-001 has `status: planned`. Plan: add a new class `MoveValidator` in `src/main/java/game/MoveValidator.java` that rejects moves of more than one tile, and wire it into `MoveHandler`. Test strategy: a unit test per rejected case. Produce the task table.
