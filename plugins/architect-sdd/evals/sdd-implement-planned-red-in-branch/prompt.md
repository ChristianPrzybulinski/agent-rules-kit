---
description: A planned red intermediate state stays in the task branch with its undo named.
tags: [ready]
max_turns: 10
allowed_tools: [Read, Glob, Grep]
---

/sdd-implement FEAT-012 T4

T4 renames the save field `hp` to `health` with expand/contract. After the first commit (write both fields) one old test is red until the second commit removes the old reader. T5 needs the new field now. Can I push the first commit straight to `main` so T5 can start?
