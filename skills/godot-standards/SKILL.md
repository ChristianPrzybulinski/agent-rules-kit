---
name: godot-standards
version: "2.0"
description: Applies Godot 2D standards — statically typed GDScript, scene composition, signals, physics separation, versioned saves. Use on `*.gd`, `*.tscn` or `project.godot`. Do not use for importing external art (skill asset-import) or pixel-art editing (skill krita).
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

References: `references/godot-4-versions.md` — supported Godot versions; `references/networking-transports.md` — transport comparison.

## When working with Godot 2D

1. Check `project.godot`, existing scene structure and scripts.
2. Statically typed GDScript (`: Type`); official style: `snake_case` for variables/functions/files, `PascalCase` for classes/nodes.
3. Prefer signals over direct calls between nodes; `get_parent()` for game logic is forbidden.
4. `_physics_process(delta)` for movement/physics; `_process(delta)` for animations/visuals; `call_deferred` to avoid intermediate physics states.
5. Cache references in `_ready`; avoid heavy per-frame work; avoid long `_ready` code — delegate to well-named functions.
6. `@export` for editor-tunable parameters, documented with a comment above.
7. Scenes small and reusable — composition over deep inheritance; Groups identify nodes without coupling; separate visuals, physics and logic.
8. `preload` for reusable scenes/resources, `load` for dynamic ones; TileMap/TileSet for 2D maps — never place tiles manually.
9. Global state centralized in autoloads; save as JSON or a custom versioned Resource — never a Node reference.
10. Game rules and state testable in isolation: the domain lives in autoloads/pure classes; scenes/nodes are adapters.

## Project structure

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
