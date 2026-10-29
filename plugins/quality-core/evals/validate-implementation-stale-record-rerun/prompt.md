---
description: A recorded proof whose input changed after it ran is re-run, not reused.
tags: [ready]
max_turns: 10
allowed_tools: [Read, Glob, Grep, Bash, Skill]
---

Is this done? Request: "`src/app.gd` has no TODO left". The proof is recorded in `.proof/todo-check.log`. The work is committed in this repository.
