# Godot coding references

Facts and commands for writing and testing GDScript in a Godot 4 2D client. The always/never for `*.gd`, `*.tscn` and `project.godot` is rule `godot.md`; design (server authority, transports, codec, frame budget) is skill `sdd-plan`, reference `godot/README.md`.

## How to use

1. Before writing GDScript, read `gdscript-4-pitfalls.md`; when unsure of an API, open its class page before the call.
2. Before committing a scene or script, read `scenes-and-generated-files.md` for `*.uid`, `*.import` and `.tscn` conflicts.
3. A game rule: build it as `testable-game-logic.md` says and run the suite: gdUnit4 by default, `godot --headless --path . -s addons/gdUnit4/bin/GdUnitCmdTool.gd -a res://tests -c --ignoreHeadlessMode`; GUT only when the project `AGENTS.md` says so, `-s addons/gut/gut_cmdln.gd -gdir=res://tests -ginclude_subdirs -gexit`. A run that executes zero tests is a failure.
4. Boot proof: the command and pattern of rule `godot.md` (the `boot` recipe, `../recipes.md`, or the import then the `--quit` log grep); the import builds every resource and the script-class cache, and `--headless` is required without a GPU. Report the literal output of both and of the test run.
5. Lint: `gdformat --check` and `gdlint` over every `.gd` outside `addons/` (config `.gdlintrc` from the kit; CI job `lint` in `ci-godot.yml`).
6. Engine or CI version questions: `godot-4-versions.md`.

## Contents

| File | Scope |
|---|---|
| [`gdscript-4-pitfalls.md`](gdscript-4-pitfalls.md) | Godot 3 to 4 syntax table and the hallucinated-API rule |
| [`scenes-and-generated-files.md`](scenes-and-generated-files.md) | what to commit, UID conflicts, scene ownership |
| [`testable-game-logic.md`](testable-game-logic.md) | `RefCounted` rule classes, injected clock and RNG, gdUnit4 suites |
| [`godot-4-versions.md`](godot-4-versions.md) | the project pin, the godot-ci image, `TileMapLayer` since 4.3 |
