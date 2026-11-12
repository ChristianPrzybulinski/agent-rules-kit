---
name: krita
description: Krita pixel-art workflow. Use when editing pixel art, retouching sprites or defining sprite export. Not for Godot import (skill asset-import).
argument-hint: "[setup | export | spritesheet | automate]"
triggers:
  - user
disable-model-invocation: true
allowed-tools:
  - read
  - exec
---

# Krita

The agent guides the human GUI and prepares deterministic external scripts; it does not automate Krita interaction.

## 1. Set up pixel art

Use exact sprite dimensions, 8-bit RGBA, Pixel Art brush with no antialiasing, one-pixel grid/snap and integer zoom. Load the project palette and separate animatable parts/shadows by layer.

## 2. Export sprites

Export PNG with alpha preserved and no rescaling. Name `<entity>_<animation>_<direction>_<frame>.png`; keep editable `.kra` in LFS and exclude `.kra~` backups.

Place source under `assets/`; Godot import targets `res://resources/sprites/` with nearest filtering as the project's Godot `AGENTS.md` describes (dev-godot template project-agents-godot-2d).

## 3. Build sprite sheets reproducibly

Export frames, then run `platforms/kits/godot/scripts/make_spritesheet.py` to create the sheet and frame/hash/pivot manifest. Record `hframes`/`vframes` for Godot.

## 4. Automate only verified transformations

Use Pillow/ImageMagick scripts for repeated recolor/crop/resize/background removal after checking installation. Record inputs, outputs and hashes per the `git-lfs-and-binaries` reference in skill `git`; never remove one color globally without per-set preview/decision.

Done when: source/export formats are correct, frame names and transparency are stable, batch transforms are reproducible and the deliverable is ready for asset import.
