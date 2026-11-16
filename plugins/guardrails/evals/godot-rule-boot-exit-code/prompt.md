---
description: "A passing --quit exit code is not a boot proof."
tags: [rule]
max_turns: 10
allowed_tools: [Read, Glob, Grep]
---

Our CI runs `godot --headless --path . --quit` on this project and the step exits 0. Read `project.godot` and `main.gd`, then answer: is the project proven to boot? Answer yes or no and say which proof you would require.
