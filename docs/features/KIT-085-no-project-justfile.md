---
id: KIT-085
title: "No project justfile: skill sdd-implement runs the kit's just modules directly"
status: done
confirmed: "2026-11-16 (owner, kit session chat; issue #320 and its comment)"
issue: "#320"
pr: "#349"
---

# KIT-085 — No project justfile: skill sdd-implement runs the kit's just modules directly

## Problem and evidence

[FACT] Since KIT-081 stage 1b (14.0.0) `sync-project.sh` wrote `import '~/.ai-kit/platforms/kits/just/<profile>.just'` into a starter `justfile` in each profile folder, `--check` failed while a justfile lacked that line, and the `ci-godot.yml` and `ci-java.yml` templates ran `just <recipe>` through it. The owner, 2026-11-16: "justfile nao importa, usa direto do kit, nao tem pq ter outro arquivo", then: "essa é a ideia do KIT, termos skills pra abstrair a chamada de scripts". A project never calls kit scripts; a kit skill finds the profile and runs the work.

[FACT] just 1.58.0 runs a module with no project justfile: `just -f ~/.ai-kit/platforms/kits/just/godot.just -d client --dry-run editor` prints `godot --path . --editor`, and the recipe runs with `client/` as its working folder (`test_just_modules.py`). `-d` alone is refused: it needs `-f`.

## Change

- Skill choice: `sdd-implement`, with a new reference `references/recipes.md`. The profile schema gives the `tests` section to the `implement` reader (`x-read-by`), and `test-gates.md` § 3 in this skill already owns "the checks before done", which the always-on rules point at. CONTRIBUTING says to extend the skill that owns a topic before adding one. The reference finds the folder's stack with `profile.py resolve --section stacks --json <repo>` (the profile's `stacks`, else the `CLAUDE.md` marker), runs `just -f ~/.ai-kit/platforms/kits/just/<stack>.just -d <repo>/<folder> <recipe> [args]`, runs every stack of a folder with several, and lets a command the profile's `tests` section sets replace the recipe for the same check. `SKILL.md` § 2 Prove and `test-gates.md` § 3 name it.
- `platforms/tools/sync_just.py` (`write|check`; `preflight` is gone with nothing left to refuse) writes no justfile and requires no import. `write` removes only what an older sync wrote, as a regular file reached without a symbolic link: a starter `justfile` recognized by its whole text (the comment lines of the KIT-074 or the stage 1b starter and one kit import line), the marked `kit.just` copies, and it still rewrites a stale `import 'kit.just'` line in a single-profile folder. A justfile with any other content, a project comment included, stays whole, with a `sync: kept` line when it imports a kit module. `check` fails on a starter or copy left and on a stale `kit.just` line.
- `sync-project.sh` no longer runs the preflight and its header and summary say "no project justfile".
- The `ci-godot.yml` and `ci-java.yml` templates run `just -f "$AI_KIT_DIR/platforms/kits/just/<profile>.just" -d . <recipe>`; the spec-tools action keeps linking `~/.ai-kit` for a project justfile of its own.
- The AGENTS templates list the recipes in a Commands table and name skill `sdd-implement`; rule `godot.md`, `living-docs.md`, `task-pr.md`, the godot step reference and the kit READMEs and `docs/projects.md` name the recipe and the skill instead of `just <recipe>`.
- `check_kit.py` § 14: an AGENTS template names its recipes in the Commands table (`test` and `verify` among them, each defined by its module) and skill `sdd-implement`, and no `just <recipe>`; a CI template runs each recipe with `-f` naming its profile's module and `-d`; `recipes.md` names the command shape.

## Proof

`bash platforms/tools/check.sh`, `bash platforms/tools/smoke.sh`, `python3.12 -B platforms/tools/run_tests.py --layer unit,contract` and `--layer integration --changed-from origin/main`; new or changed tests in `test_sync_just.py` (no justfile written, the starters removed, a project's justfile kept whole, links never followed, the skill names the command), `test_sync_dev_standards.py`, `test_just_modules.py` (each module run with `-f`/`-d`; the § 14 fixtures), `test_kit_workflows.py` and `test_consumer_fixture.py`.

## History

- 2026-11-16: confirmed (owner, issue #320); direction changed to a kit skill the same day (#320 comment).
- 2026-11-16: implemented on `feat/kit-085-no-project-justfile`.
- 2026-11-22: status done (#320 closed by #349; #439).
