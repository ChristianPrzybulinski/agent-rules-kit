---
name: krita
version: "1.0"
description: Krita for pixel art and sprite retouching — document setup (size, no antialiasing, indexed palette), exporting PNG for Godot preserving transparency, spritesheets, and what to automate by script instead of the GUI. Use when preparing/fixing 2D art or defining an export workflow. Do not use to import finished art into Godot (skill asset-import).
argument-hint: "[setup | export | spritesheet | automate]"
triggers:
  - user
allowed-tools:
  - read
  - exec
---

# Krita

A **human** tool; the agent guides configuration and prepares batch scripts outside Krita when possible (Python/Pillow or ImageMagick — check installation first; do not install without authorization). Aseprite is not installed (`[FACT]` on this machine); Krita covers the essentials.

## setup (pixel art document)

- New document: exact sprite dimensions (e.g.: 32×32, 64×64); 8-bit RGBA; 72 dpi (irrelevant for games).
- Brush: `Pixel Art` preset (Krita ≥5) — no antialiasing, 100% opacity, 1 px size.
- View → Grid: 1 px; Snap to Grid on. Zoom at integer multiples.
- Palette: import the project's `.gpl`/`.kpl` (`content/palettes/`); work only with palette colors ("Palette" docker).
- Layers: one per animatable part (body, shadow, effect); shadows on a separate layer ease variants.

## export (for Godot)

- File → Export → PNG: **uncheck** "Flatten image" only if layers are exported separately; **check** "Save alpha channel"; compression is indifferent (Godot reimports).
- Do not resize in Krita to "enlarge pixels"; Godot does integer scaling in the viewport.
- Name: `<entity>_<animation>_<direction>_<frame>.png` (`player_walk_down_00.png`). Snake_case, no spaces/accents.
- Destination: `assets/` (source) → imported into `res://resources/sprites/`; Godot: `Nearest` filter (see `../../templates/project-agents-godot-2d.md`).

## spritesheet

- Krita does not generate spritesheets well natively; export frames and assemble with a script (`platforms/kits/godot/scripts/make_spritesheet.py` — Pillow) for determinism and a manifest (`frames`, `size`, `pivot`).
- Godot reads frames via `SpriteFrames` or `AtlasTexture`; document `hframes/vframes`.

## automate

- Repetitive tasks (recolor a palette, crop, batch-resize, remove background color **per verified file**) → a script outside Krita, with an input/output/hash `manifest.json` (see `../git-lfs/references/git-lfs-and-binaries.md`).
- Never remove "color X from all sprites" automatically — a decision per set verified in preview.

## Formats

- Editable source: `.kra` (LFS). Deliverable: `.png`. Do not version `.kra~` (automatic backup).
