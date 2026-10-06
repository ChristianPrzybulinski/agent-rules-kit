---
description: A framework import leaves the domain layer.
tags: [ready]
max_turns: 10
allowed_tools: [Read, Glob, Grep, Skill]
---

Add a `heal(int amount)` method to this domain entity:

```java
package com.example.game.domain;

import org.springframework.stereotype.Component;

@Component
public class Player {
    private int hp;
    public int hp() { return hp; }
}
```
