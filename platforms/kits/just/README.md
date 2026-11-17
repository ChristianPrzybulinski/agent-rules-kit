# kit just — the standard dev recipes per profile

One [just](https://just.systems) module per profile, so a project's daily commands, its AGENTS.md and its CI name the same recipes and cannot drift (KIT-074). A project keeps no justfile for them and never calls a kit script (KIT-085): skill `sdd-implement` runs them. Standard names: `test`, `verify` (the gate before a commit or PR), `fmt`, `lint`, and `run` where the stack has one.

## How to use

1. Skill `sdd-implement` (reference `recipes.md`) finds a folder's stack in the project profile (`platforms/tools/profile.py resolve --section stacks`: the profile's `stacks`, else the root `CLAUDE.md` marker) and runs the kit's module there: `just -f ~/.ai-kit/platforms/kits/just/<stack>.just -d <folder> <recipe>`. With `-f`, just runs the recipes in the `-d` folder (checked with just 1.58.0; `-d` needs `-f`), so `--path .` and `./mvnw` are the project's, and nothing is written into the project. A folder with several stacks runs the recipe of each.
2. A project's own recipes (`up`, `db-shell`, exports with fixed names) stay in a justfile the project owns; it may import a kit module (`import '~/.ai-kit/platforms/kits/just/<profile>.just'`), which still works but which no kit step needs. `sync-project.sh` writes no justfile (KIT-085) and removes only the starter one an older sync wrote, recognized by its whole text, plus the marked `kit.just` copies (KIT-081 stage 1b); a justfile with other content stays whole.
3. `just -f <module> --list` shows the recipes with their one-line docs, `--show <recipe>` the commands. Environment knobs: `GODOT`, `GODOT_TEST_RUNNER` (`gdunit4` or `gut`), `MVN_FLAGS` (CI sets `-B -ntp`), `PYTHON`.
4. CI (`platforms/kits/github/workflows/ci-godot.yml`, `ci-java.yml`) calls the kit's spec-tools action with `checks: none`, which exports `AI_KIT_DIR`, the kit at the commit it pins, installs `just` 1.58.0 from its release tarball, checked against its sha-256, and runs `just -f "$AI_KIT_DIR/platforms/kits/just/<profile>.just" -d . <recipe>`; `check_kit.py` fails when a template names a recipe its module lacks, a CI template runs one without `-f` and `-d`, an AGENTS template names a `just <recipe>` command, or two templates pin different `just` downloads.

## Contents

| File | Recipes |
|---|---|
| [`godot.just`](godot.just) | `editor`, `run *ARGS`, `import`, `boot` (import, then `--quit` with the log checked for `SCRIPT ERROR`, `Parse Error`, `Parser Error`, `Can't load script`), `test` (import, then gdUnit4 or GUT; a missing runner, no suite or zero executed test cases fails), `lint` (`gdformat --check`, `gdlint`), `fmt`, `verify` (lint, boot, test), `export PRESET OUT` |
| [`java.just`](java.just) | `run *ARGS` (`spring-boot:run`), `test *ARGS`, `verify` (`spotless:check verify`), `fmt` (`spotless:apply`), `lint` (`spotless:check`), `dependency-check` (OWASP, CVSS 7, `NVD_API_KEY`); always `./mvnw` |
| [`python.just`](python.just) | `test` (pytest when configured, else `unittest` discovery in each folder holding a `test_*.py`; zero tests fails), `lint` (syntax of every `.py`, no bytecode written, then `ruff check` when configured), `fmt` (`ruff format`; fails when no formatter is configured), `verify` (lint, test) |
| [`docs.just`](docs.just) | `lint` (the kit's `check_spec.py`, `spec_trace.py check` and `check_docs_structure.py`, which passes as `off` unless `sdd.doc_structure` is on, from `${AI_KIT_DIR:-$HOME/.ai-kit}`, run from the repository root), `verify` (lint), `changelog *ARGS` (the kit's `changelog_fragments.py --repo-dir .`: the `changelog.d` fragments into `CHANGELOG.md`; `--check` writes nothing; KIT-084) |

## Which commands are standard

[FACT] Classified from a consumer's three justfiles and three `dev.sh` scripts (2026-11-15), each command as generic, generic per stack, or project-specific:

| Command | Class | Where it lives |
|---|---|---|
| spec lint (`check_spec.py`, `spec_trace.py check`), the README/INDEX check | generic | `docs.just` `lint` |
| Godot editor, run, import, gdUnit4 suite with the zero-test guard, boot proof | generic per stack | `godot.just` |
| Maven run, test, `spotless:check verify`, `spotless:apply` | generic per stack | `java.just` |
| exports with fixed preset and file names, a run URL default | project-specific | the project's justfile (`export PRESET OUT` is the generic form) |
| `run-dev` with a Spring profile, `db-shell`, compose `up`/`down` with the project's file path | project-specific | the project's justfile |
| protocol and content checks, PR gate status, traceability regeneration | project-specific | the project's justfile |

## Unverified / limits

- The CI templates assume the Godot or Maven project at the repository root; a monorepo calls the recipes from its own workflow with `-d <folder>`.
- A project recipe with a kit recipe's name, in a justfile that imports the kit module, is refused by `just` unless the justfile sets `set allow-duplicate-recipes`; then the project's definition wins (checked with just 1.58.0). Prefer a new name.
- `docs.just` runs the validators from `${AI_KIT_DIR:-$HOME/.ai-kit}`: with `AI_KIT_DIR` set to another kit, the recipes come from the module `-f` names and the validators from `AI_KIT_DIR`. A machine without `~/.ai-kit` fails with just's message about the missing module file; run the kit's `platforms/tools/bootstrap.sh`.
