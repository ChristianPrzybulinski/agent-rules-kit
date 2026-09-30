---
description: Rules for 2D game development with Godot and GDScript. Load for `*.gd`, `*.tscn` or `project.godot`.
trigger: model_decision
---

# Godot 2D

## Project organization

```text
project/
├── project.godot
├── autoload/           # Global singletons (GameManager, Audio, Save)
├── common/             # Reusable components
├── entities/           # Character, enemy, item scenes
├── levels/             # Maps/stages
├── ui/                 # Menus, HUD, screens
├── resources/          # Sprites, sounds, fonts, tilesets
└── tests/              # Integration/scene tests when applicable
```

## GDScript

- Official GDScript style: `snake_case` for variables/functions/files, `PascalCase` for classes/nodes.
- Use static typing (`: Type`) whenever possible.
- Avoid long `_ready` code; delegate to well-named functions.
- Signals are preferred over direct calls between nodes for decoupling.
- Use `@export` for editor-tunable parameters.
- Document `@export` properties with comments above them.

## Nodes and scenes

- Small, reusable scenes. Prefer composition over deep inheritance.
- Respect the SceneTree hierarchy; avoid `get_parent()` for game logic.
- Use Groups to identify multiple nodes without coupling.
- Separate visuals, physics and logic when possible.

## Physics and processing

- Use `_physics_process(delta)` for movement/physics; `_process(delta)` for animations/visual effects.
- Avoid heavy per-frame operations. Cache references in `_ready`.
- Use `call_deferred` when needed to avoid intermediate physics states.

## Resources

- Prefer preloaded `Resource`s (`preload`) for reusable scenes and scripts.
- Keep textures and sprites organized under `res://resources/`.
- Use TileMap/TileSet for 2D maps; avoid placing tiles manually.

## Save and state

- Centralize global state in autoloads.
- Save as JSON or a custom Resource; version the save format.
- Do not store node references in the save.

## Clean Architecture in Godot

- The game domain (rules, state, events) can live in autoloads/pure classes.
- Scenes/nodes are adapters/interface; game rules must be testable in isolation.
