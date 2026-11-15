---
description: "Three independent checks, one of them long, load skill parallelize."
tags: [trigger]
max_turns: 10
allowed_tools: [Read, Glob, Grep, Bash, Skill]
append_system_prompt: "Independent steps or long commands → load skill `parallelize`. Send independent steps in the same turn or run them in the background; sequence only what depends on a result, shares a resource or has an external effect."
---

Run the test suite, the linter and the type checker, and tell me what fails.
