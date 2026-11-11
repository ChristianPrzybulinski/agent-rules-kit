---
description: A third mode reshapes the design instead of adding another flag.
tags: [ready]
max_turns: 10
allowed_tools: [Read, Glob, Grep, Skill]
---

We now need a third reward mode, "event", that doubles coins on weekends. Implement it in this function with the smallest change.

```java
public int coinsFor(Battle battle, boolean legacyMode, boolean tournamentMode) {
    int coins = battle.baseCoins();
    if (legacyMode) {
        coins = coins / 2;
        if (battle.isBoss()) { coins += 10; }
    }
    if (tournamentMode && !legacyMode) {
        coins = coins * 3;
    }
    return coins;
}
```
