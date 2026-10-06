---
description: Godot 3 script is rewritten with Godot 4 syntax and types.
tags: [ready]
max_turns: 10
allowed_tools: [Read, Glob, Grep, Skill]
---

Rewrite this Godot 3 script for Godot 4 and show the full result:

```gdscript
extends KinematicBody2D
export var speed = 100
onready var sprite = $Sprite
func _physics_process(delta):
    yield(get_tree(), "idle_frame")
    var v = Vector2()
    move_and_slide(v * speed)
```
