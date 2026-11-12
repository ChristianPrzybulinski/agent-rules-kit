---
description: Before a PR that changes a GDScript rule, the answer names the advisory coverage command and leaves out a suite that reads the autoload list.
tags: [ready]
max_turns: 10
allowed_tools: [Read, Glob, Grep, Skill]
---

Our Godot 4 client keeps each game rule in a pure `RefCounted` class with gdUnit4 suites under `res://tests`. On this branch (base `origin/main`) I changed `features/battle/damage_rule.gd` and every suite is green. Before I open the PR, what exactly do I run to see which lines and branches of the functions I changed no suite reaches? One suite, `tests/app/autoload_order_test.gd`, asserts the exact autoload list of `project.godot`.
