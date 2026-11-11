---
description: A threshold copied into two files moves to one owner instead of two edits.
tags: [ready]
max_turns: 10
allowed_tools: [Read, Glob, Grep, Skill]
---

Change the evolve level from 30 to 25. Show me the diff.

```gdscript
# features/party/party_panel.gd
func can_show_evolve_button(level: int) -> bool:
    return level >= 30

# app/network/evolve_request.gd
func is_valid_evolve(level: int) -> bool:
    if level < 30:
        return false
    return true
```
