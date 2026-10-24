---
description: Require authentication evidence before recommending login.
tags: [ready]
max_turns: 6
allowed_tools: [Read, Glob, Grep, Skill]
---

Help me interpret three independent PR-access incidents without running commands:

1. Through a working network path, the authentication status check explicitly
   reports that the active account's credential is invalid.
2. Authentication succeeds, but a PR request returns a permission error.
3. Authentication succeeds, but a PR request reports that its API rate limit
   was exceeded.

For each incident, explain whether I should log in again and the next step.
Do not ask me to paste credentials or change any account state yourself.
