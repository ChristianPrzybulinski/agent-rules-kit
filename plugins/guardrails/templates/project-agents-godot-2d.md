# AGENTS.md — Godot 4 (2D, GDScript)

Replace the passages between [brackets]. The AI Kit's global rules already apply; keep in this file only what the agent cannot infer.

## Stack

- Godot [4.x] (confirm in `project.godot` → `config/features`). Statically typed GDScript required.
- Tests: [gdUnit4 | GUT] in `tests/`. Renderer: [Forward+ | Mobile | Compatibility]. Movement model: [A physics bodies | B grid/tile-step] (see "Movement model").
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
godot --headless --path . --import                                # import assets, build the script-class cache (CI)
! godot --headless --path . --quit 2>&1 | grep -Eq 'SCRIPT ERROR|Parser Error'   # boot proof: --quit exits 0 after a script error
godot --path . --headless -s addons/gdUnit4/bin/GdUnitCmdTool.gd -a res://tests -c --ignoreHeadlessMode   # run gdUnit4 (default)
godot --path . --headless -s addons/gut/gut_cmdln.gd -gdir=res://tests -ginclude_subdirs -gexit             # run GUT (alternative); delete the runner not used
godot --path . --headless --export-release "[preset]" build/[name]   # export
```

## Patterns (condition → action)

- Declare a variable/parameter/return → always typed (`var speed: float = 120.0`, `func hit(dmg: int) -> void`).
- Reference a child node → `@onready var sprite: Sprite2D = $Sprite2D`; never `get_node` inside `_process`.
- Communicate between non-parent nodes → signal (or an `EventBus` autoload). `get_parent()` for game logic is forbidden.
- Move an entity → follow the "Movement model" section below; never mix physics bodies and tile steps in one entity.
- Override `_ready`/`_process` in a child class → call `super()`.
- Tuning parameter → `@export` with a range and a one-line comment above.
- Shared behavior (health, damage, state) → a component in `common/` composed into the scene; not deep inheritance.
- Instantiate a scene repeatedly → `preload` into a constant; consider pooling if >50 instances/frame.
- Map → `TileMapLayer` (4.3+); separate layers for floor/collision/decoration.
- Collision → option A: name layers/masks in `project.godot` (`layer_names/2d_physics`), never magic numbers; option B: read collision from the same map data the rules validate; no physics layers for grid entities.
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

## Movement model

Declared choice: [A | B]. Decision record: [docs/spec/decisions/DEC-nnn-*.md | docs/adr/nnnn-*.md]. Delete the option not chosen.

### Option A, physics bodies

- Velocity is set on the body and `move_and_slide()` is called in `_physics_process(delta)`.
- Animation and visuals run in `_process(delta)`.
- Never move a physics body from `_process`.

### Option B, grid/tile-step (server-authoritative when online)

- Authoritative position: integer tile `[Vector2i]` owned by `[server | GameState]`.
- Input -> `[move_intent]` with a direction only; the client predicts at most one step and reconciles on `[entity_moved | move_rejected]` (a rejection snaps back).
- Presentation tweens/lerps the sprite toward the confirmed tile in `_process(delta)`; the camera follows the displayed position.
- `CharacterBody2D`/`move_and_slide()` are not used for grid entities; collision comes from the map data the rules validate.

Never mix the two models in one entity; presentation never changes the authoritative position.

## Git & PR

- `.tscn`/`.tres` are text: review the diff; UID conflicts → reimport, do not hand-edit.
- Commit `.godot/` **never**; commit `*.import` **always**.
- Conventional Commits; PR with a GIF/screenshot when the change is visual.
- CI runs the suite headless and fails when the runner is missing or zero tests execute; never skip tests to get a green run (see the kit `ci-godot.yml`).

## Boundaries

- Always: run the two boot-proof commands from Commands after touching assets or scripts; test a scene in isolation (F6) before the whole stage.
- Ask first: change `project.godot` (renderer, physics, input map); add an addon; change the save format.
- Never: mix the two movement models in one entity, or let presentation change the authoritative position; `get_parent()` for game logic; editing `.godot/`.

## More

- Mechanics and balancing: `docs/design.md`. Decisions: `docs/adr/`.
