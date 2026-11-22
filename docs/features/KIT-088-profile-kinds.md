---
id: KIT-088
title: "The profile gains project.kind presets and the keys the game and FEAT-only flows read"
status: done
confirmed: "2026-11-16 (owner, chat of the kit session: \"concordo\" with the game-profile evaluation §§ 1-5 and 8.2-8.4, filing \"Sim, abra\"; the E § 17 scope, \"Sim, faça\")"
issue: "#329"
pr: "#344"
---

# KIT-088 — The profile gains project.kind presets and the keys the game and FEAT-only flows read

## Problem and evidence

[FACT] The game-profile evaluation (`KIT-GAME-PROFILE-EVALUATION-2026-11-16.md` in the owner's workspace, "E"),
§§ 3, 8.2, 10 and 17, backlog id G1:

1. A game project needs the SDD flow to behave differently in a few places (optional vision sections, an `Assets` Plan
   section, greybox and polish passes, playtest acceptance), and the kit repository itself runs a FEAT-only flow (no
   NEED, no REQ, no task table, a record for a big change only, `docs/features/`, `KIT-NNN`) that no key can express
   (E § 10.2). `plan_sections` has no `Assets`.
2. Setting four to seven keys by hand per project repeats one choice, the kind of project (E § 3, alternative B).
   Forked skills per kind were rejected: a project never copies a step to change it (E § 3, alternative C).
3. KIT-087 deferred `spec_root` and `release` as speculative with one project; the kit's `docs/features/` and Stratics'
   milestone versions are the second layouts (E §§ 10.2, 13.2).

## Change

- `platforms/ci/schemas/profile.schema.json`:
  - `project.kind`: `business` (default), `game`, `tooling`. Only the resolver reads it. Its `x-presets` holds each kind's
    values: `business` none; `game` `sdd.vision_sections: [Pillars, Core loop, Direction, References]`, the nine Plan
    sections plus `Assets`, `sdd.passes: [greybox, polish]`, `sdd.acceptance: playtest`,
    `evidence.visual_approval: owner`; `tooling` `sdd.flow: feat-only`, `needs: false`, `task_table: false`,
    `record_when: big-change`, `pr_unit: feat`, `plan_sections: [Tests, Risks]`, `release: manual`.
  - New keys, each with a default that keeps today's behaviour: `sdd.vision_sections` (`[]`, the optional `spec.md`
    sections by heading), `sdd.passes` (`[]`; items `greybox`, `polish`), `sdd.acceptance` (`captures` | `playtest`),
    `sdd.flow` (`full` | `feat-only`), `sdd.task_table` (`true`), `sdd.record_when` (`always` | `big-change`),
    `sdd.id_prefix.feature` (`FEAT`), the top-level `spec_root` (`docs/spec`) and `release.versioning`
    (`semver` | `milestone`).
  - `Assets` joins the `plan_sections` enum here and in `spec.schema.json`, whose legacy `sdd:` block validates it;
    no default lists it.
- `platforms/tools/profile.py`: a key resolves to the project's value (`.ai-kit.yaml` or its legacy home), else its
  kind's preset, else its schema default; an unknown kind fails as any value outside its enum. `defaults()` follows
  the kind. `spec_root` moves the legacy `sdd:` home and the journeys folder to `<spec_root>/` when the caller names
  no spec folder; top-level scalars (`kit`, `spec_root`) resolve generically.
- `check_spec.py --params` is unchanged: it prints the keys `spec.schema.json` defines, so the new profile-only keys
  stay out, and a spec without `project.kind` resolves as before.
- Docs: `sdd-parameters.md` (the `Assets` value and a pointer to the schema for the new keys and presets, at 60 lines),
  `docs/projects.md`, `platforms/ci/README.md`, `platforms/tools/README.md`, the CHANGELOG.
- Not here: no skill reads the new keys yet (KIT-089 onwards and KIT-087 P2); the kit's own `.ai-kit.yaml` keeps no
  `kind` (KIT-101); the spec-index template per kind (KIT-089).

## Proof

[FACT] On branch `feat/kit-088-profile-kinds`, macOS:

- `platforms/ci/validations/test_profile.py` gains `KindPresets` (each preset's values, explicit and legacy keys over
  the preset, an unknown kind, values outside each new key's range, `spec_root` moving the legacy home), two contract
  tests (each preset names known keys with valid non-default values; `Assets` in both enums, off by default) and two
  command-line tests (the presets resolve alike with and without pyyaml, `-S`; an unknown kind fails in both).
- `python3.12 -B -m unittest platforms/ci/validations/test_profile.py`: `Ran 43 tests`, OK; the same module and
  `test_check_spec.py` under `/usr/bin/python3` 3.9.6: `Ran 116 tests`, OK.
- `run_tests.py --layer unit,contract`: `Ran 270 tests`, `OK (skipped=16)` (gdtoolkit);
  `run_tests.py --layer integration --changed-from origin/main`: `Ran 222 tests`, `OK (skipped=1)` (a non-UTF-8 file
  name this file system refuses).
- `check.sh` and `check.sh --links` (system `python3` 3.9.6): `check: OK (1 plugins, 18 skills, 11 rules, 13
  templates, 15 readmes, 160 links, 63 hook cases, 18 shell scripts)`, `plugin indexes are current`.
- Not run here: the evals for the edited reference `sdd-parameters.md`, and the resolver on a real consumer checkout.

## History

- 2026-11-16: confirmed (owner, kit chat; issue #329 and its E § 17 update).
- 2026-11-16: implemented on `feat/kit-088-profile-kinds`.
- 2026-11-22: status done (#329 closed by #344; #439).
