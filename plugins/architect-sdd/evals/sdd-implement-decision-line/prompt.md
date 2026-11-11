---
description: A choice the spec did not fix is recorded as one line in the FEAT's Decisions section.
tags: [ready]
max_turns: 10
allowed_tools: [Read, Glob, Grep]
---

/sdd-implement FEAT-012 T2

T2 (spawn table) is done and its proof passed; PR #88 is open. The spec did not say how to store the table, and I chose a sorted array with binary search over a Dictionary because the encounter roll needs a cumulative weight lookup. Close the task: what do I write in the FEAT file?
