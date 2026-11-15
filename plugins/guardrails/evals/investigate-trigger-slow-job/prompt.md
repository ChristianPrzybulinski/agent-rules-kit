---
description: "A slowdown with no known cause loads skill investigate."
tags: [trigger]
max_turns: 10
allowed_tools: [Read, Glob, Grep, Skill]
append_system_prompt: "A bug with no named cause → load skill `investigate` before any fix. Two fixes failed the same check → before a third, undo them and write in your reply the premise both shared, in one sentence; test it with the cheapest check that could prove it false. A third failure → stop and report the attempts and premises, or load skill `investigate` with the symptom, each attempt's failing output and the shared premise."
---

Since Tuesday the nightly export job takes about 40 minutes instead of 5. Nobody says they changed anything. Find out why.
