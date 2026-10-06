---
description: Performance budget rules for a Godot 2D client - project-set targets, measure-first rules and per-frame prohibitions.
kind: detail
---

# Godot 4 - performance budget

The budget is a project parameter set, not an engine fact. Declare it before the test and report results as literal numbers.

## Parameters the project sets

- Parameter: target frame time (16.6 ms at 60 FPS) and physics tick rate.
- Parameter: node count per scene and draw calls.
- Parameter: memory for the preloaded world working set.

## Rules

- Measure before optimizing with the `Performance` monitors and the debugger Monitors tab; name the monitor used in the PR.
- Pool objects only after a measured allocation cost; no speculative pooling.
- One generated `TileMapLayer` per map layer, not per tile (4.3 floor in `./godot-4-versions.md`).
- `Nearest` texture filtering for pixel art, set once in `project.godot`, not per sprite.
- Texture atlases or sprite sheets over many small textures.
- `_physics_process` for simulation, `_process` for visuals; no per-frame `get_node`, string formatting or `load()` - preload or cache instead.
