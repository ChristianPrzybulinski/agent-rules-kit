---
description: A passing --quit exit code is not a boot proof.
tags: [ready]
plugins: [../.., ../../../core]
max_turns: 10
allowed_tools: [Read, Glob, Grep, Skill]
---

Our CI runs `godot --headless --path . --quit` and the step exits 0. Is the project proven to boot? Answer yes or no and say which proof you would require.
