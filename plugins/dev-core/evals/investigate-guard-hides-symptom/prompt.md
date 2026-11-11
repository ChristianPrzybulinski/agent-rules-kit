---
description: A null check that only hides a crash is not accepted as the fix.
tags: [ready]
max_turns: 10
allowed_tools: [Read, Glob, Grep, Skill]
---

Players crash on login with `Invalid get index 'name' (on base: 'Nil')` in `inventory_panel.gd:88`, where `var item := inventory.get_item(slot)` is followed by `item.name`. I plan to add `if item == null: return` before line 88 and close the bug. Is that the fix?
