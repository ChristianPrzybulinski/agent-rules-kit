---
description: Battle damage moves into a pure function that receives the clock and randomness.
tags: [ready]
max_turns: 10
allowed_tools: [Read, Glob, Grep, Skill]
---

Where should the damage calculation live? It is in a Godot node today and its tests are flaky.

```gdscript
extends Node2D

func apply_hit(attacker: Creature, target: Creature) -> void:
    var crit := randf() < 0.1
    var night := Time.get_datetime_dict_from_system()["hour"] >= 20
    var damage := attacker.attack * (2 if crit else 1) + (5 if night else 0)
    target.hp -= damage
    $Hud.show_damage(damage)
```
