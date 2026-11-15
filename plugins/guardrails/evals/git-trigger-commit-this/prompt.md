---
description: "Plain \"commit this\" on an uncommitted change loads skill git."
tags: [trigger]
max_turns: 10
allowed_tools: [Read, Glob, Grep, Bash, Skill]
append_system_prompt: "Before a commit, PR or release → load skill `git`."
---

Commit this change.
