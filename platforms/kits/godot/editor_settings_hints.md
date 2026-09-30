# Godot 4 — editor settings for 2D pixel-art

Factual; each item is an Editor/Project Setting → path.

- **Nearest filter**: Project Settings → `rendering/textures/canvas_textures/default_texture_filter` = `Nearest`. Without it, pixelated sprites blur when scaled.
- **Grid snap**: 2D editor toolbar → snap ON; 1px grid (or the tile size) in `interface/inspector` / toolbar Snap Options.
- **Pixel snapping**: Project Settings → `rendering/2d/snap/snap_2d_transforms_to_pixel` = ON; `snap_2d_vertices_to_pixel` = ON for vertices.
- **Viewport/stretch**: `display/window/stretch/mode` = `canvas_items`, `aspect` = `keep` for a fixed base resolution.
- **Movement**: use `_physics_process(delta)` and `move_and_slide()`; do not move physical bodies in `_process`.
- **Signals**: connect via code (`button.pressed.connect(...)`) or the editor; keep `_on_<node>_<signal>` handler names.
- **Export**: `export_presets.cfg` defines the presets (`Windows Desktop`, `macOS`) used by CI (`platforms/kits/github/workflows/ci-godot.yml`).
