---
name: godot-standards
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

Names, functions and the smallest change: read skill `code-standards`. Test gates and coverage: read skill `testing`.

References: `references/godot-4-versions.md` (versions), `references/networking-transports.md` (transport DEC), `references/authority-and-prediction.md`, `references/network-codec.md`, `references/testable-game-logic.md`, `references/gdscript-4-pitfalls.md`, `references/scenes-and-generated-files.md`, `references/performance-budget.md` (online 2D client; read the one your task touches).

## 1. Inspect the project

Read `project.godot`, scene ownership and neighboring scripts before editing. Confirm the fixed engine version against the project and the version reference.

## 2. Write typed GDScript

- Type parameters, returns and stored values; use `snake_case` for files/functions/variables and `PascalCase` for classes/nodes.
- Cache node references in `_ready`; move substantial initialization into named functions.
- Use `@export` only for editor-tunable values and document the reason/range above it.

## 3. Separate scene responsibilities and respect the movement model

- Prefer scene composition and signals over deep inheritance or parent traversal for game rules.
- Keep visuals, physics and rules separate; domain state stays in pure classes/autoload services that tests can instantiate without a scene.
- The movement model is a project decision, declared in the repository `AGENTS.md` (a "Movement model" section or a movement pattern line) and its decision record. Read it before writing or reviewing movement code; if it is missing, ask, do not assume physics.
  - Option A, physics bodies: `CharacterBody2D`/`RigidBody2D`, velocity set and `move_and_slide()` called in `_physics_process(delta)`; collision via named layers/masks; visuals and animation in `_process`.
  - Option B, grid/tile-step: the authoritative position is an integer tile coordinate owned by the game rules (the server when online); input becomes a step intent, the client predicts at most one step and reconciles on confirm/reject; presentation tweens or lerps the sprite toward the confirmed tile in `_process`; no `CharacterBody2D`, no `move_and_slide()`, collision read from the same map data the rules validate.
  - Never mix the two in one entity, and never let presentation (tween, lerp, camera) change the authoritative position.
- Defer mutations that would invalidate a physics iteration (`call_deferred`, `set_deferred`) whenever physics bodies are in use.

## 4. Manage resources and state

- Use `preload` for fixed reusable resources and `load` for dynamic choices.
- Use `TileMapLayer`/TileSet for maps rather than manually placed tiles.
- Centralize true global state in a small autoload; persist versioned JSON/Resource data, never Node references.

## 5. Verify

Boot proof, two commands in this order: `godot --headless --path . --import` (imports every resource, builds the script-class cache, quits; `--headless` is mandatory without a GPU), then `! godot --headless --path . --quit 2>&1 | grep -Eq 'SCRIPT ERROR|Parser Error'` (the exit code of `--quit` is 0 after a script error, so a match is the failure). Then run the project test command.
Report the literal output of all three; a `SCRIPT ERROR`, `Parser Error` or import error is a failure even when the exit code is 0.

Test runner: gdUnit4 by default (`-s addons/gdUnit4/bin/GdUnitCmdTool.gd -a res://tests -c --ignoreHeadlessMode`), GUT only when the project `AGENTS.md` says so (`-s addons/gut/gut_cmdln.gd -gdir=res://tests -ginclude_subdirs -gexit`). A run that executes zero tests, or a missing runner, is a failure, never a skip. Game rules live in pure `RefCounted` classes with scene-free tests; scene tests are integration only (skill `testing`, section 1).
Before pushing, run `gdformat --check` and `gdlint` over every `.gd` outside `addons/` (config: `.gdlintrc` from the kit; CI job `lint` in `ci-godot.yml`); fix formatting with `gdformat <file>`, never by hand.

Done when: changed scripts are typed, scene dependencies use composition/signals, rules are testable without nodes, and headless import plus tests pass, and movement code follows the declared movement model.
