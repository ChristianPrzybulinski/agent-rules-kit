---
description: Always/never constraints for GDScript, scenes and project.godot; the coding and design detail is in the sdd-implement and sdd-plan godot references.
trigger: glob
globs:
  - "**/*.gd"
  - "**/*.tscn"
  - "**/project.godot"
paths:
  - "**/*.gd"
  - "**/*.tscn"
  - "**/project.godot"
---

Always/never for `*.gd`, `*.tscn` and `project.godot`; names, functions and errors: rule `code.md`; tests: rule `tests.md`. Detail: skill `sdd-implement`, reference `godot/README.md` (pitfalls, generated files, testable rules, versions); skill `sdd-plan`, reference `godot/README.md` (authority, transports, codec, budget).

- Always: read `project.godot`, the scene's owner and the neighbouring scripts before an edit; the engine version is the project pin (`config/features` and the repo `AGENTS.md`), never a local `godot --version`.
- Always: Godot 4 syntax only: `@onready`, `@export`, `await`, `instantiate()`, `signal_name.connect(callable)`. Never `onready var`, `export`, `yield`, `instance()`, `connect("name", ...)`.
- Always: typed GDScript: `var speed: float = 120.0`, `func hit(dmg: int) -> void`; an untyped variable, parameter or return is a defect. `snake_case` files, functions and variables; `PascalCase` classes and nodes.
- Never: `@warning_ignore` to hide an untyped or unused warning (type it or delete the code); any other sits on the narrowest line with a comment naming why.
- Always: cache node references with `@onready` or in `_ready`, never a `get_node` per frame; `@export` only for an editor-tuned value, with its reason or range in a comment above it.
- Never: `get_parent()`, an ancestor lookup or a sibling path (`$"../Other"`) to apply a game rule; a child reports up by signal and its parent calls down, or use the project's `EventBus` autoload; a node gets what it needs through an `@export` or a `Callable` its parent sets.
- Always: gameplay reads discrete input in `_unhandled_input`, so an event the UI handled does not also act; `_input` only for a handler that must see the event before the GUI; held actions are polled in `_physics_process` (physics bodies) or `_process`.
- Always: visuals, physics and rules apart: game state and rules live in `RefCounted` classes with `class_name`, built with `.new()` and tested without a scene; no `get_node`, autoload, `Time.*` or `randi()` inside a rule (inject the clock and a seeded `RandomNumberGenerator`).
- Never: an authoritative game rule on the client; the client sends intent, predicts only what the repo `AGENTS.md` allows and reconciles on the server's answer.
- Always: the movement model the repo `AGENTS.md` declares (a "Movement model" section or line); missing, ask, never assume physics. Physics bodies: `CharacterBody2D`/`RigidBody2D`, `velocity` and `move_and_slide()` in `_physics_process(delta)`, collision by named layers and masks. Grid or tile-step: the authoritative position is an integer tile the rules own, input becomes a step intent, the client predicts at most one step and presentation tweens toward the confirmed tile; no `CharacterBody2D` or `move_and_slide()`.
- Never: both movement models in one entity, or a tween, lerp or camera that writes the authoritative position.
- Always: defer a mutation that would invalidate a physics step (`call_deferred`, `set_deferred`) when physics bodies are in use.
- Always: `preload` for a fixed resource, `load` for a dynamic choice; maps in `TileMapLayer` (one node per layer), never `TileMap` or hand-placed tiles.
- Always: unsaved data with no Inspector use is a `RefCounted`, saved or Inspector-edited data a `Resource`, a `Node` only when it needs the tree; persist versioned JSON or `Resource` data, never a `Node` reference.
- Never: a new autoload except for a self-contained system that owns its data and changes no other node; helpers are `static func` on a `class_name` script.
- Always: new or changed logic ships with a gdUnit4 test under `tests/` (GUT only when the repo `AGENTS.md` says so); a run with zero executed tests or no runner is a failure, never a skip.
- Always: a source's generated neighbours (`*.uid`, `*.import`; `*.translation` follows the project's rule, ignored by default) go in the same commit as the source; they are implicit in a task's `Files` and never listed there, so the project's gates config lists them in `generated_neighbours` (the `pr_gates.py` default is none).
- Never: edit `.godot/`, a `.uid` file or a generated `*.import` by hand.
- Always: boot proof before "done": `just boot` where the folder's justfile imports the kit's godot module, else `godot --headless --path . --import` then `! godot --headless --path . --quit 2>&1 | grep -Eq "SCRIPT ERROR|Parse Error|Parser Error|Can't load script"` (`--quit` exits 0 after a script error, so a match is the failure); then the project test command; paste the literal output of all three.
- Always: before a push, `gdformat --check` and `gdlint` over every `.gd` outside `addons/`; fix formatting with `gdformat <file>`, never by hand.
