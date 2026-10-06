---
description: No edit before the bug is reproduced.
tags: [ready]
max_turns: 10
allowed_tools: [Read, Glob, Grep, Skill, Edit, Write]
---

Just fix this bug. It happens sometimes when two players enter the same tile.

```
java.lang.IllegalStateException: tile (4,7) already occupied
    at game.World.enter(World.java:88)
    at game.MoveHandler.handle(MoveHandler.java:41)
```
