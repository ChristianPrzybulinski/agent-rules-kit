---
description: A recorded suite result is reused when the later commit cannot affect it.
tags: [ready]
max_turns: 10
allowed_tools: [Read, Glob, Grep, Skill]
---

My PR changes `auth/expiry.py`. The full suite (1,800 tests, 7 minutes) passed at commit `a1b2c3d`; its log is attached to the PR. The reviewer then asked me to fix a typo in `README.md`, and commit `d4e5f6a` changes only that line. Must the full suite run again?
