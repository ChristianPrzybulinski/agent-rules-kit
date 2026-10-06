---
description: GDScript 3.x to 4.x pitfall table and the hallucinated-API rule for Godot 4 code. Load when writing or reviewing GDScript.
kind: fact
verified: "2026-10-06"
sources:
  - https://docs.godotengine.org/en/stable/tutorials/migrating/upgrading_to_godot_4.html
  - https://docs.godotengine.org/en/stable/classes/class_characterbody2d.html
  - https://docs.godotengine.org/en/stable/classes/class_tilemaplayer.html
---

# Godot 4 - GDScript pitfalls

| 3.x (wrong today) | 4.x | note |
|---|---|---|
| `onready var` | `@onready var` | annotations replace keywords |
| `export var` | `@export var` | same for the other export hints |
| `tool` | `@tool` | annotation |
| `yield(obj, "sig")` | `await obj.sig` | or `await get_tree().process_frame` |
| `scene.instance()` | `scene.instantiate()` | PackedScene |
| `KinematicBody2D` + `move_and_slide(vel)` | `CharacterBody2D`, set `velocity`, call `move_and_slide()` | no argument; reads `velocity` |
| `TileMap` | `TileMapLayer` | one node per layer, Godot 4.3+ |
| `connect("sig", self, "m")` | `sig.connect(m)` | typed signal object |
| `deg2rad` | `deg_to_rad` | same for `rad2deg` |
| `rand_range` | `randf_range` / `randi_range` | global scope |
| `OS.get_ticks_msec` | `Time.get_ticks_msec` | Time singleton |
| `PoolStringArray` | `PackedStringArray` | all Pool* became Packed* |
| `setget` | `set`/`get` property syntax | `var x: T: get = g, set = s` |
| `get_node` in `_process` | cache the node in `_ready` | per-frame lookup is a budget bug |

## Hallucinated APIs

- Rule: when unsure, open the class page under docs.godotengine.org/en/stable/classes/ before writing the call.
- The three most common tells: a method that exists on a different class, `await` on a non-signal non-coroutine, a signal name the node does not declare.
- Proof still required: the boot check (`--import` then the `SCRIPT ERROR` grep, skill section 5) catches parser errors but not wrong runtime calls, so a unit test is still required.

godot-guard (github.com/brocolriri/godot-guard, MIT, scripts/api_guard.py): evaluated 2026-10-06, not a gate. Free CLI scans for Godot 3 idioms (92 rules) but flags gdUnit4 fluent chains continued on a line starting with "." as the Godot 3 "._ready()" call; blocking hooks are a paid tier. Use it manually on suspicious generated code; gdlint plus the import proof are the gates.
