---
description: "An endpoint that serves files by a user-supplied path loads skill security."
tags: [trigger]
max_turns: 10
allowed_tools: [Read, Glob, Grep, Skill]
append_system_prompt: "A trust-boundary change, a secret or a dependency CVE → load skill `security`. Every commit: no hardcoded secret, validated input, parameterized queries, authorization per action **and** entity, errors that keep internals private."
---

Add an endpoint to our Flask app that lets a logged-in user download one of their uploaded files by passing the file path in the query string.
