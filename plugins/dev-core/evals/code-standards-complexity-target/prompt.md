---
description: A changed GDScript function above CC 10 is split or tested.
tags: [ready]
max_turns: 10
allowed_tools: [Read, Glob, Grep, Skill]
---

My PR changes `apply_status` (I added the `"frozen"` branch). It works and the tests pass. Anything to change before it merges?

```gdscript
func apply_status(target: Creature, status: String, turns: int) -> void:
	if target.is_fainted():
		return
	if status == "burn":
		if target.has_type("fire"):
			return
		target.hp -= max(1, target.max_hp / 16)
	elif status == "poison":
		if target.has_type("poison") or target.has_type("steel"):
			return
		target.hp -= max(1, target.max_hp / 8)
	elif status == "sleep":
		if target.status != "" or turns <= 0:
			return
		target.sleep_turns = clamp(turns, 1, 3)
	elif status == "frozen":
		if target.has_type("ice"):
			return
		if randf() < 0.2:
			target.status = ""
			return
	target.status = status
	if target.hp <= 0:
		target.faint()
```
