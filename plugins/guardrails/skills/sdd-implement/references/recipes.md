---
description: "Runs a folder's test, lint, boot or verify recipe from the kit's just module for its profile stack. Load at Prove or when a doc names a recipe."
kind: fact
verified: "2026-11-16"
sources:
  - "https://just.systems/man/en/"
  - "https://github.com/casey/just/releases/tag/1.58.0"
---

# Stack recipes

A project keeps no justfile for the kit's recipes and never calls a kit script (KIT-085). This skill runs the recipe: the AGENTS.md of a project and the kit's templates name a recipe (`boot`, `test`, `verify`) and this reference, never a command.

## 1. Find the folder's stack

1. `PROFILE resolve --section stacks --json <repo>` (`KIT` and `PROFILE`: `../../session/references/project-profile.md`): folder (`.` the root) → stack or list of stacks. Without `.ai-kit.yaml` it reads the profile list of the root `CLAUDE.md` sync marker and says so on stderr.
2. The folder is the longest key that is the changed file's folder or one of its parents. No key matches → the folder has no stack: say so and run no recipe.
3. A non-zero exit (an invalid profile, a conflict) → report its lines and stop; never guess a stack.

## 2. Run the recipe

```bash
just -f "$KIT/platforms/kits/just/<stack>.just" -d <repo>/<folder> <recipe> [args]
```

- `-f` names the kit's module, `-d` the folder the recipe runs in; without `-d`, just runs it in the module's own folder, the kit's. `-d` alone is refused (it needs `-f`).
- `just -f <module> --list` lists the recipes with their one-line docs, `--show <recipe>` the commands. Knobs: `GODOT`, `GODOT_TEST_RUNNER` (`gdunit4` or `gut`), `MVN_FLAGS`, `PYTHON`; `docs` reads its validators from `${AI_KIT_DIR:-$HOME/.ai-kit}`.
- A folder with several stacks runs the recipe of each stack whose module defines it.
- A command the profile's `tests` section sets for the stack (`profile.py resolve --section tests --json <repo>`) is the project's own and runs as written, from the folder, in place of the recipe for the same check: `unit` → `test`, `broad` → `verify`, `boot` → `boot`, `lint` → `lint`; `integration` and `fmt` have no recipe and run where the row's Proof names them.
- A person who types it by hand may alias it in their own shell (`alias kg='just -f ~/.ai-kit/platforms/kits/just/godot.just -d .'`); the project commits no alias and no justfile.

## 3. Which recipe

| Need | Recipe | Stacks |
|---|---|---|
| the TDD loop of `test-gates.md` § 3 | `test` (`test -Dtest=X` for one Java test) | godot, java, python |
| the linters | `lint` | all four |
| the boot proof before "done" | `boot` | godot |
| the gate before a commit or PR | `verify` | all four |
| format | `fmt` | godot, java, python |
| run or open the app | `run`, `editor` | godot, java (`run`) |
| spec lint, changelog fragments | `lint`, `changelog` | docs |

- Paste the literal output. A green run counts only when the runner's summary shows tests executed (`test-gates.md` § 3).
- A recipe that fails because the kit is missing (no `KIT`) → run the kit's `platforms/tools/bootstrap.sh`; never copy a module into the project.
- [FACT] On just 1.58.0 the `godot`, `java`, `python` and `docs` modules run with `-f`/`-d` and no project justfile (`test_just_modules.py`).
