---
name: godot-standards
version: "2.1"
description: Godot 2D and typed GDScript standards. Use when editing *.gd, *.tscn, project.godot or GDScript scenes. Not for asset import (skill asset-import).
triggers:
  - user
  - model
allowed-tools:
  - read
  - grep
  - glob
  - exec
  - edit
---

# Godot 2D Standards

References: `references/godot-4-versions.md` for supported versions and `references/networking-transports.md` when a project DEC compares transports.

## 1. Inspect the project

Read `project.godot`, scene ownership and neighboring scripts before editing. Confirm the fixed engine version against the project and the version reference.

## 2. Write typed GDScript

- Type parameters, returns and stored values; use `snake_case` for files/functions/variables and `PascalCase` for classes/nodes.
- Cache node references in `_ready`; move substantial initialization into named functions.
- Use `@export` only for editor-tunable values and document the reason/range above it.

## 3. Separate scene responsibilities

- Prefer scene composition and signals over deep inheritance or parent traversal for game rules.
- Use `_physics_process` for physics/movement and `_process` for visuals; defer mutations that would invalidate a physics iteration.
- Keep visuals, physics and rules separate; domain state stays in pure classes/autoload services that tests can instantiate without a scene.

## 4. Manage resources and state

- Use `preload` for fixed reusable resources and `load` for dynamic choices.
- Use `TileMapLayer`/TileSet for maps rather than manually placed tiles.
- Centralize true global state in a small autoload; persist versioned JSON/Resource data, never Node references.

## 5. Verify

Run `godot --path . --headless --quit` and the project test command. Treat parser/import errors as failures and report the literal output.

Done when: changed scripts are typed, scene dependencies use composition/signals, rules are testable without nodes, and headless import plus tests pass.
