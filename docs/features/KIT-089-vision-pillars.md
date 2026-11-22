---
id: KIT-089
title: "spec.md gets a template per project kind, with pillars, counted scope and an out-of-scope triage"
status: done
confirmed: "2026-11-16 (owner, chat of the kit session: \"concordo\" with the game-profile evaluation §§ 1-5 and 8.2-8.4, filing \"Sim, abra\"; the E § 17 scope, \"Sim, faça\")"
issue: "#330"
pr: "#348"
---

# KIT-089 — spec.md gets a template per project kind, with pillars, counted scope and an out-of-scope triage

## Problem and evidence

[FACT] The game-profile evaluation (`KIT-GAME-PROFILE-EVALUATION-2026-11-16.md` in the owner's workspace, "E"),
§§ 2 (stages 0 and 1), 4, 8.2, 16 and 17, backlog id G2:

1. `spec.md` had Vision, First-delivery scope and Out of scope only: no pillars, core loop, direction or reference
   works, and a scope line `- [item]` with no count (E § 2 stage 0, § 4.2).
2. `sdd-specify` decide read `spec.md` but had no rule against its Out of scope list, and nothing checked that a NEED
   serves a product principle (E § 4.1, 4.3); the NEED template had no line for the experience or the pillar (E § 2
   stage 1).
3. No artifact said which register (user, PO, technical) it is written in (E § 16, owner rule 2026-11-16).
4. KIT-088 (#329) added `project.kind` and `sdd.vision_sections`, which nothing read yet.

## Change

- Templates: `spec-index.md` becomes `spec-index-business.md`, and `spec-index-game.md` joins it. Both carry the
  optional sections Pillars (product principles for business, design pillars for a game), Core loop, Direction and
  References, a counted First-delivery scope, an Out of scope line format (`why; never | after <milestone>`) and a
  header comment naming the register. `sdd-constitution` keeps the sections `sdd.vision_sections` lists and deletes
  the others. The game file's `sdd:` block sets `plan_sections` at the game preset (`Assets` on): the explicit legacy
  block resolves before the kind preset, so a copy of the business block would hide it.
- `platforms/kits/sdd/init-spec.sh`: picks the template by the profile's `project.kind` (`profile.py resolve --section
  project`): `game` gets the game file, any other kind the business one; an invalid profile stops before the copy.
- `sdd-constitution` § 3: reads `sdd.vision_sections` from the resolved profile and writes the vision sections, the
  counted scope and the Out of scope lines.
- `sdd-specify` § 1: a NEED that hits an Out of scope line closes `rejected` (never) or `parked` (later), citing the
  line; while `spec.md` has `## Pillars`, a `new`, `improvement`, `content` or `decision` NEED names its pillar, and
  one serving none closes the same way; a `fix` or `platform` NEED writes `Pillar: —`. `spec-need.md` gains the
  `Experience` line and the Triage `Pillar` line.
- `sdd-check`: row C13 (functional scope, high).
- `sdd-process.md` § Register: the E § 16 table for the artifacts that exist (NEED, `spec.md` vision, journey,
  REQ, DEC, FEAT, glossary); each template's header comment points to it, except `spec-journey.md` (KIT-086 edits
  journeys). The project-layout tree became one paragraph to keep the reference at 60 lines.
- `rules/spec.md`, `sdd-parameters.md`, `check_kit.py` (`SPEC_MAP`), `platforms/kits/sdd/README.md`: the new names.
- Not here: the process and enabler rows of the register (with their artifacts, G3a and G10), C26 (KIT-091), and the
  orphan `docs/design.md` and `docs/adr/` pointer in `project-agents-godot-2d.md`, which KIT-085 edits in parallel.

## Proof

[FACT] On branch `feat/kit-089-vision-pillars`, macOS, Python 3.12:

- `platforms/ci/validations/test_init_spec.py` (new, integration): the game kind copies the game file; no profile,
  `business` and `tooling` copy the business file; an invalid kind stops before any copy; an existing `spec.md` is
  kept. `Ran 4 tests`, OK.
- `test_check_spec.py` `test_template_block_passes` checks both templates: each passes `check_spec.py`, the business
  block resolves to the kit defaults, the game block to them with `plan_sections` at the game preset.
- `run_tests.py --layer unit,contract`: `Ran 270 tests`, `OK (skipped=16)` (gdtoolkit);
  `run_tests.py --layer integration --changed-from origin/main`: `Ran 213 tests`, `OK (skipped=1)` (a non-UTF-8 file
  name this file system refuses).
- `check.sh`: `check: OK (1 plugins, 18 skills, 11 rules, 14 templates, ...)`, `plugin indexes are current`, with five
  `paragraph duplicated` warnings: the two kind templates share the cover, Regimes, Glossary, Architecture and
  reading-order paragraphs, since each is a whole file `init-spec.sh` copies.
- `shellcheck -x` and `/bin/bash -n` (3.2) on `init-spec.sh`: clean.
- Evals: `claude plugin eval plugins --tag trigger --runs 1 --ablation none --no-publish --trust-plugin --scaffold`:
  six cases, each 1.00 (no case covers `sdd-constitution`, `sdd-specify`, `sdd-check` or the `spec` rule).
- Not run: the skills on a real project (a game `spec.md` written by `sdd-constitution`, a NEED triaged against
  Pillars), and the trigger suite at `--runs 5`.

## History

- 2026-11-16: confirmed (owner, kit chat; issue #330 and its E § 17 update).
- 2026-11-16: implemented on `feat/kit-089-vision-pillars`.
- 2026-11-22 amend (#442): check_kit.py no longer warns on paragraphs shared only among the spec-index kind variants; a copy anywhere else still warns.
- 2026-11-22: status done (#330 closed by #348; #439).
