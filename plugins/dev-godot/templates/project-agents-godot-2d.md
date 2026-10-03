# AGENTS.md — Godot 4 (2D, GDScript)

Replace the passages between [brackets]. The AI Kit's global rules already apply; keep in this file only what the agent cannot infer.

## Stack

- Godot [4.x] (confirm in `project.godot` → `config/features`). Statically typed GDScript required.
- Tests: [GUT | gdUnit4] in `tests/`. Renderer: [Forward+ | Mobile | Compatibility].
- Pixel art: `rendering/textures/canvas_textures/default_texture_filter = Nearest` (see `project.godot`).

## Structure

```text
res://
├── project.godot
├── autoload/      # GameState, EventBus, AudioManager, SaveManager (singletons)
├── common/        # reusable components (HealthComponent, Hitbox, StateMachine)
├── entities/      # player/, enemies/, items/ — each: .tscn + .gd + sprites
├── levels/        # stage scenes + TileMapLayers
├── ui/            # menus, HUD, screens
├── resources/     # .tres (balancing data, stats), fonts, themes
├── assets/        # sprites, audio (raw source)
└── tests/
```

## Commands

```bash
godot --path . --editor                         # open editor
godot --path . --headless --quit                # import assets/validate project (CI)
godot --path . --headless -s addons/gut/gut_cmdln.gd   # run GUT (adjust to the framework)
godot --path . --headless --export-release "[preset]" build/[name]   # export
```

## Patterns (condition → action)

- Declare a variable/parameter/return → always typed (`var speed: float = 120.0`, `func hit(dmg: int) -> void`).
- Reference a child node → `@onready var sprite: Sprite2D = $Sprite2D`; never `get_node` inside `_process`.
- Communicate between non-parent nodes → signal (or an `EventBus` autoload). `get_parent()` for game logic is forbidden.
- Move a body → `_physics_process(delta)`; `CharacterBody2D.move_and_slide()`. Visual/animation → `_process(delta)`.
- Override `_ready`/`_process` in a child class → call `super()`.
- Tuning parameter → `@export` with a range and a one-line comment above.
- Shared behavior (health, damage, state) → a component in `common/` composed into the scene; not deep inheritance.
- Instantiate a scene repeatedly → `preload` into a constant; consider pooling if >50 instances/frame.
- Map → `TileMapLayer` (4.3+); separate layers for floor/collision/decoration.
- Collision → name layers/masks in `project.godot` (`layer_names/2d_physics`); never use magic numbers.
- Save → versioned pure data (Dictionary/Resource) with `save_version`; never a Node reference.
- Feature touches `.gd` + `.tscn` + `.tres` + `project.godot` → read all before changing one.

Example — component with a signal:

```gdscript
class_name HealthComponent
extends Node

signal died
signal changed(current: int, max_value: int)

## Maximum health; tunable per enemy in the editor.
@export_range(1, 999) var max_health: int = 10
var current: int

func _ready() -> void:
    current = max_health

func take_damage(amount: int) -> void:
    current = maxi(current - amount, 0)
    changed.emit(current, max_health)
    if current == 0:
        died.emit()
```

## Git & PR

- `.tscn`/`.tres` are text: review the diff; UID conflicts → reimport, do not hand-edit.
- Commit `.godot/` **never**; commit `*.import` **always**.
- Conventional Commits; PR with a GIF/screenshot when the change is visual.

## Boundaries

- Always: run `--headless --quit` after touching assets; test a scene in isolation (F6) before the whole stage.
- Ask first: change `project.godot` (renderer, physics, input map); add an addon; change the save format.
- Never: logic in `_process` that belongs in `_physics_process`; `get_parent()` for game logic; editing `.godot/`.

## More

- Mechanics and balancing: `docs/design.md`. Decisions: `docs/adr/`.
