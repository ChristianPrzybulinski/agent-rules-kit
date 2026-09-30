---
name: godot-standards
version: "1.0"
description: Applies Godot 2D project standards with GDScript, nodes, signals and autoloads. Use on `*.gd`, `*.tscn` or `project.godot`.
triggers:
  - user
  - model
allowed-tools:
  - read
  - grep
  - glob
  - exec
---

# Godot 2D Expert

## When working with Godot 2D

1. Check `project.godot`, existing scene structure and scripts.
2. Use typed GDScript (`: Type`) and the official style (snake_case/PascalCase).
3. Prefer signals over direct calls between nodes.
4. Use `_physics_process(delta)` for movement/physics; `_process(delta)` for visual effects.
5. Organize into `autoload/`, `entities/`, `levels/`, `ui/`, `resources/`, `common/`.
6. Cache references in `_ready`. Avoid `get_parent()` for logic.
7. Use `@export` for tunable parameters and document above them.
8. Keep scenes small and reusable; prefer composition.
9. Test game logic in isolation when possible.
10. Do not store node references in saves.

## Standard checks

- `preload` for static resources; `load` for dynamic ones.
- Groups to identify multiple nodes without coupling.
- TileMap/TileSet for 2D maps.
- Autoloads for global state and managers.
