---
description: A surviving mutant on a changed line is killed, deleted or named even when the 80% gate is green.
tags: [ready]
max_turns: 10
allowed_tools: [Read, Glob, Grep, Skill]
---

PIT says mutation score 86% on `battle.domain` (threshold 80%), so the gate is green. One mutant survived, and it sits on a line this PR changed:

```
CaptureRule.java:42  changed conditional boundary  `if (hp < threshold)` -> `if (hp <= threshold)`  SURVIVED
```

The gate passes. Can I merge?
