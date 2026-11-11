---
description: A squash commit body states why, what changed and the proof.
tags: [ready]
max_turns: 10
allowed_tools: [Read, Glob, Grep, Skill]
---

Write the squash commit message (title and body) for this PR:

- Problem: the shop accepted a purchase with a negative quantity (issue #57).
- Change: `ShopService.buy` rejects quantity < 1; new boundary tests for 0, 1 and -1.
- Proof: `./mvnw -q test -Dtest=ShopServiceTest` → `Tests run: 9, Failures: 0`.
