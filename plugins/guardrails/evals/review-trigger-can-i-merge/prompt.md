---
description: "A merge-readiness question on a branch loads skill review."
tags: [trigger]
max_turns: 10
allowed_tools: [Read, Glob, Grep, Bash, Skill]
append_system_prompt: "\"Is it done?\", or about to claim done or open a PR → load skill `review`. Report what you did not test, run or read in the diff as \"unverified\", never as done."
---

Can I merge this branch? The author says the age validation is finished and the tests pass.
