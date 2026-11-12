---
description: After green suites on a GDScript rule, the answer names the advisory mutation command, feeds it the coverage report and skips the cache after a Godot upgrade.
tags: [ready]
max_turns: 10
allowed_tools: [Read, Glob, Grep, Skill]
---

The gdUnit4 suites pass for my change to `features/inventory/stack_rule.gd` in our Godot 4 client (base `origin/main`), and the line and branch coverage report of this commit is at `/tmp/cov.json`. What exactly do I run to check whether the suites would catch a flipped `<` or a dropped call in the functions I changed? I ran the same check an hour ago on this commit; the only change since then is Godot 4.7.1 → 4.7.2 on this machine.
