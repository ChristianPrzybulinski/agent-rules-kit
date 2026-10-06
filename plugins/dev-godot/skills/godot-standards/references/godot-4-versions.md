---
description: Godot 4.x versions (project pin in project.godot and AGENTS.md, matching godot-ci image, TileMapLayer since 4.3). Load when configuring a Godot project or CI.
kind: fact
verified: "2026-09-29"
sources:
  - https://docs.godotengine.org/en/stable/about/release_policy.html
  - https://github.com/godotengine/godot/releases
---

# Godot 4 — versions

- The project pins its engine: `project.godot` `config/features` (for example `PackedStringArray("4.7", "Mobile")`, minor only) and the project `AGENTS.md` (the stratics-client one states `Godot 4.7.2` on its first line). Never read the version from a local `godot --version`; read those two files. The local binary's version is local state and belongs in `docs/machine.local.md`.
- CI image: `barichello/godot-ci:<project version>`; the kit workflow `platforms/kits/github/workflows/ci-godot.yml` takes it as the `godot-version` input (default `4.7.2`). The tag must exist on Docker Hub for the pinned version: verify against https://hub.docker.com/r/barichello/godot-ci/tags before bumping it.
- Release policy: Godot follows feature releases (~4.x, every few months) + patch releases (4.x.y). Minor upgrades may break project compatibility — read the changelog before migrating. Source: https://docs.godotengine.org/en/stable/about/release_policy.html
- `TileMapLayer` (separate node, replaces layers inside `TileMap`): introduced in Godot **4.3**. In new projects use `TileMapLayer`; `TileMap` exists for compatibility.
- Downloads/releases: https://godotengine.org/download and https://github.com/godotengine/godot/releases.
