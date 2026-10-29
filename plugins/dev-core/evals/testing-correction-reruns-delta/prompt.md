---
description: A correction to covered code re-runs the tests it touches.
tags: [ready]
max_turns: 10
allowed_tools: [Read, Glob, Grep, Skill]
---

My PR changes the token-expiry check in `auth/expiry.py`. The focused auth tests and the full suite (1,800 tests, 7 minutes) passed at commit `a1b2c3d`. Review then found an off-by-one in the same expiry comparison, and I fixed it in commit `d4e5f6a`; nothing else changed. Which checks must run again, and can the earlier full-suite result still count?
