---
description: A changed GDScript function the duplicate finder pairs with existing code gets one owner, or the PR names why not.
tags: [ready]
max_turns: 10
allowed_tools: [Read, Glob, Grep, Skill]
---

The duplicate finder printed one line for my PR:

```
1.000 app/network/stats_validator.gd:152 _integer app/network/group_validator.gd:121 _integer
```

`_integer` is the helper I copied into the new stats validator from the group validator:

```gdscript
static func _integer(value: Variant, minimum: int, maximum: int) -> bool:
	if typeof(value) != TYPE_INT and typeof(value) != TYPE_FLOAT:
		return false
	return (
		is_finite(float(value))
		and value == floorf(float(value))
		and value >= minimum
		and value <= maximum
	)
```

Five other validators already have their own copy that differs only in `maximum: float = INF`. The finder's output is advisory, so I plan to merge as is. OK?
