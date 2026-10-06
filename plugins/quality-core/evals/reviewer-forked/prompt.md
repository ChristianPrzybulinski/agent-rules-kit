---
description: validate-implementation runs forked and reports in the reviewer format.
tags: [ready]
max_turns: 10
allowed_tools: [Read, Glob, Grep, Bash, Skill]
---

Is this done? Request: "add a greet() function that returns hello". It is in `greet.py`, committed in this repository. The proof is `python3 -c 'import greet; assert greet.greet() == "hello"'`.
