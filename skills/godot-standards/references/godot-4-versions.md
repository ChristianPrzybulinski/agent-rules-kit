---
description: Godot 4.x versions (4.7.2 installed, matching CI image, TileMapLayer since 4.3, release policy). Load when configuring a Godot project or CI.
trigger: model_decision
verified: "2026-09-29"
sources:
  - https://docs.godotengine.org/en/stable/about/release_policy.html
  - https://github.com/godotengine/godot/releases
---

# Godot 4 — versions

- Version installed on this machine: **4.7.2.stable** (`godot --version` → `4.7.2.stable.official.ed1daf0bf`).
- Matching CI image: `barichello/godot-ci:4.7.2` (tag exists on Docker Hub).
- Release policy: Godot follows feature releases (~4.x, every few months) + patch releases (4.x.y). Minor upgrades may break project compatibility — read the changelog before migrating. Source: https://docs.godotengine.org/en/stable/about/release_policy.html
- `TileMapLayer` (separate node, replaces layers inside `TileMap`): introduced in Godot **4.3**. In new projects use `TileMapLayer`; `TileMap` exists for compatibility.
- Downloads/releases: https://godotengine.org/download and https://github.com/godotengine/godot/releases.
