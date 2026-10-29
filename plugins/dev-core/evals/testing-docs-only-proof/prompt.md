---
description: A prose-only change runs the doc checks, not the code suites.
tags: [ready]
max_turns: 10
allowed_tools: [Read, Glob, Grep, Bash, Skill]
---

I fixed two typos in `docs/guide.md` and committed them. This repository has a full suite (`./run-tests.sh`, about 40 minutes) and a link checker (`python3 tools/check_links.py docs`). What must run before I call it done?
