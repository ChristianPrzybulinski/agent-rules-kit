---
description: A match whose arms each make one call is left alone.
tags: [ready]
max_turns: 10
allowed_tools: [Read, Glob, Grep, Skill]
---

A reviewer says this `match` is too long and should become a dictionary of callables before my PR merges. My PR only adds the `"trade"` arm. Should I refactor it now?

```gdscript
func _dispatch(kind: String, payload: Dictionary) -> void:
    match kind:
        "move": _on_move(payload)
        "chat": _on_chat(payload)
        "battle": _on_battle(payload)
        "party": _on_party(payload)
        "bag": _on_bag(payload)
        "shop": _on_shop(payload)
        "trade": _on_trade(payload)
        _: push_warning("unknown kind %s" % kind)
```
