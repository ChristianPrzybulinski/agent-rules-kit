# Godot 4 — ajustes de editor para pixel-art 2D

Factual; cada item é Editor/Project Setting → caminho.

- **Filtro Nearest**: Project Settings → `rendering/textures/canvas_textures/default_texture_filter` = `Nearest`. Sem isso, sprites pixelados ficam borrados ao escalar.
- **Snap de grid**: toolbar do editor 2D → snap ON; grid 1px (ou o tamanho do tile) em `interface/inspector` / toolbar Snap Options.
- **Transformação de pixels**: Project Settings → `rendering/2d/snap/snap_2d_transforms_to_pixel` = ON; `snap_2d_vertices_to_pixel` = ON para vértices.
- **Viewport/stretch**: `display/window/stretch/mode` = `canvas_items`, `aspect` = `keep` para resolução base fixa.
- **Movimento**: usar `_physics_process(delta)` e `move_and_slide()`; não mover em `_process` para corpos físicos.
- **Sinais**: conectar via código (`button.pressed.connect(...)`) ou editor; manter nomes de handler `_on_<nó>_<sinal>`.
- **Export**: `export_presets.cfg` define os presets (`Windows Desktop`, `macOS`) usados pelo CI (`platforms/kits/github/workflows/ci-godot.yml`).
