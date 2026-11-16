# kit just — the standard dev recipes per profile

One [just](https://just.systems) module per profile, so a project's daily commands, its AGENTS.md and its CI name the same recipes and cannot drift (KIT-074). Standard names: `test`, `verify` (the gate before a commit or PR), `fmt`, `lint`, and `run` where the stack has one.

## How to use

1. Run `platforms/tools/sync-project.sh <repo>`: the `justfile` of each profile folder imports the installed kit's module, `import '~/.ai-kit/platforms/kits/just/<profile>.just'` (`--profile docs,godot:client,java:server` imports the godot module in `client/` and the java module in `server/`). The project holds no copy (KIT-081 stage 1b): just replaces a leading `~/` in an import path with the home folder and runs an imported recipe in the importing justfile's folder, so `--path .` and `./mvnw` are the project's.
2. The folder's own `justfile` holds that line and the project's recipes (`up`, `db-shell`, exports with fixed names). The sync writes a starter `justfile` with the line where a folder has none, rewrites in place a line that imports the `kit.just` an older sync generated (and removes that marked copy), and otherwise leaves the file alone; `--check` fails while it lacks the import. A monorepo root reaches a folder's recipes with `mod client` (`just client test`), or the developer runs `just` inside the folder. A folder with several profiles gets no import and a warning: an import path is a fixed string, a `mod` module's recipes run in the module file's folder (the kit's), and two imports define the same recipe names; import one profile's module and write the other's recipes, or give each profile its own folder.
3. `just --list` shows the recipes with their one-line docs, `just --show <recipe>` the commands. Environment knobs: `GODOT`, `GODOT_TEST_RUNNER` (`gdunit4` or `gut`), `MVN_FLAGS` (CI sets `-B -ntp`), `PYTHON`.
4. CI (`platforms/kits/github/workflows/ci-godot.yml`, `ci-java.yml`) calls the kit's spec-tools action with `checks: none`, which links `$HOME/.ai-kit` to the kit at the commit it pins (the path the import names; an import path takes no variable), installs `just` 1.58.0 from its release tarball, checked against its sha-256, and runs the recipes; `check_kit.py` fails when a template names a recipe its module lacks or two templates pin different `just` downloads.

## Contents

| File | Recipes |
|---|---|
| [`godot.just`](godot.just) | `editor`, `run *ARGS`, `import`, `boot` (import, then `--quit` with the log checked for `SCRIPT ERROR`, `Parse Error`, `Parser Error`, `Can't load script`), `test` (import, then gdUnit4 or GUT; a missing runner, no suite or zero executed test cases fails), `lint` (`gdformat --check`, `gdlint`), `fmt`, `verify` (lint, boot, test), `export PRESET OUT` |
| [`java.just`](java.just) | `run *ARGS` (`spring-boot:run`), `test *ARGS`, `verify` (`spotless:check verify`), `fmt` (`spotless:apply`), `lint` (`spotless:check`), `dependency-check` (OWASP, CVSS 7, `NVD_API_KEY`); always `./mvnw` |
| [`python.just`](python.just) | `test` (pytest when configured, else `unittest` discovery in each folder holding a `test_*.py`; zero tests fails), `lint` (syntax of every `.py`, no bytecode written, then `ruff check` when configured), `fmt` (`ruff format`; fails when no formatter is configured), `verify` (lint, test) |
| [`docs.just`](docs.just) | `lint` (the kit's `check_spec.py`, `spec_trace.py check` and `check_docs_structure.py`, which passes as `off` unless `sdd.doc_structure` is on, from `${AI_KIT_DIR:-$HOME/.ai-kit}`, run from the repository root), `verify` (lint) |

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

- The CI templates assume the Godot or Maven project at the repository root; a monorepo calls the recipes from its own workflow with `working-directory`.
- A project recipe with a kit recipe's name is refused by `just` unless the justfile sets `set allow-duplicate-recipes`; then the project's definition wins (checked with just 1.58.0). Prefer a new name.
- The import names `~/.ai-kit`, while `docs.just` runs the validators from `${AI_KIT_DIR:-$HOME/.ai-kit}`: with `AI_KIT_DIR` set to another kit, the recipes come from `~/.ai-kit` and the validators from `AI_KIT_DIR`. A machine without `~/.ai-kit` fails every recipe of that justfile with `could not find source file for import`.
