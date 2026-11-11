---
description: A long log is read through a file or subagent and the report keeps the summary and the path.
tags: [ready]
max_turns: 10
allowed_tools: [Read, Glob, Grep, Bash, Skill]
---

The nightly run wrote 12,000 lines to `ci/nightly-2026-11-10.log`. Write a short status report for the team channel about what failed.
