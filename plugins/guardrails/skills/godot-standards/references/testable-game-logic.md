---
description: Godot game rules testable without a SceneTree - RefCounted pure classes, injected clock and RNG, gdUnit4 scene-free suites.
kind: fact
verified: "2026-10-06"
sources:
  - https://godot-gdunit-labs.github.io/gdUnit4/latest/advanced_testing/cmd/
  - https://github.com/godot-gdunit-labs/gdUnit4
  - https://docs.godotengine.org/en/stable/classes/class_refcounted.html
  - https://docs.godotengine.org/en/stable/classes/class_randomnumbergenerator.html
---

# Godot 4 - testable game logic

## Pure rule classes

- Game state and rules live in `RefCounted` classes with `class_name`: no `Node`, no `get_node`, no autoload access. Nodes adapt signals and input to those classes.
- Inject a clock (an object exposing `func now_ms() -> int`) and a `RandomNumberGenerator` seeded in tests; never call `Time.*` or `randi()` inside a rule.

## gdUnit4

- Suites `extends GdUnitTestSuite`; test files live under the project tests folder, named per project convention. Parameter: default pattern `*_test.gd`.
- Instantiate pure classes with `.new()` and no scene; use the gdUnit4 scene runner only for integration tests of a `.tscn`.
- Headless runs need `--ignoreHeadlessMode`; the exact CI command and the zero-executed-tests failure rule live in `platforms/kits/github/workflows/ci-godot.yml` - cite it, do not restate it.
- Parameter: the alternative runner is GUT, only when the project `AGENTS.md` says so.

## Policy and fixtures

- Coverage policy: every game rule has a scene-free test; there is no numeric gate for GDScript (owner, 2026-11-13). Advisory measures, run from the project folder: `python3 ~/.ai-kit/platforms/tools/gd_coverage.py` (line and branch coverage per function) and `python3 ~/.ai-kit/platforms/tools/gd_mutation.py` (surviving mutants); skill `testing` § 1 says when and with which flags.
- Test fixtures live next to the suites (protocol fixtures per `./network-codec.md`); generated `*.uid` files next to test scripts are committed - see `./scenes-and-generated-files.md`.
