---
description: A workflow permission change is classified by behavior, not by file extension.
tags: [ready]
max_turns: 10
allowed_tools: [Read, Glob, Grep, Skill]
---

The only change in my PR is `.github/workflows/deploy.yml`: `permissions: contents: read` became `contents: write`. It is just a YAML file, so the docs checks are enough before I call it done, right?
