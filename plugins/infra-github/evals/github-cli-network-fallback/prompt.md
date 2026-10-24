---
description: Choose a read path after a sandbox connectivity failure.
tags: [ready]
max_turns: 6
allowed_tools: [Read, Glob, Grep, Skill]
---

I only authorized reading PR metadata. In the Codex sandbox, the PR query reports
`error connecting to api.github.com` and the remote-ref query reports
`Could not resolve host: github.com`. The GitHub connector can read PR metadata.
Explain the next action, and what to do if that connector cannot provide a needed
field. Should I log in again? Do not execute commands or change anything.
