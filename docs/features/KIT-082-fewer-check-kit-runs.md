---
id: KIT-082
title: "Fewer check_kit.py runs on kit copies, no mutations keyed to kit wording, and the GDScript tool tests run in CI"
status: done
confirmed: "2026-11-16 (owner, chat of the coordinator session on the test suite review: \"Sim, comece a parte A\")"
issue: "#311"
pr: "#312"
---

# KIT-082 — Fewer check_kit.py runs on kit copies, no mutations keyed to kit wording, and the GDScript tool tests run in CI

Part A of the coordinator's test suite review (2026-11-16, read-only, `origin/main` `2330103`); the review's other
changes (KIT-081's sync tests, a switch that skips the hook cases, the `smoke.sh` sync section) are later pull requests.

## Problem and evidence

[FACT] From the review's measured run (`run_tests.py --start platforms/ci/validations --durations 60`, 970 tests,
402 s wall on 10 workers at load average 15–25):

- 34 tests in 7 classes copy the kit and run `check_kit.py` on the copy, 36 runs, 1,549 s of the 2,967 s summed test
  time (52 %), and 28 of the 30 slowest tests; one run took 17.1 s.
- Three of them only check that the real kit passes, which the `static` job already checks on every pull request.
- The other mutations of a class are independent, yet each runs `check_kit.py` on its own copy.
- Four mutations replace literal text of a real kit file ("Not for parallelism" in `session/SKILL.md`, "load skill
  `git`." in an eval case, "just verify" and "just boot" in templates), so rewording that file breaks a test about
  something else; the session checklist test asserts phrases ("one outcome") and the Godot template test the whole
  `just --no-deps test` line.
- 54 tests skip in every CI job because none installs gdtoolkit (KIT-077 skip table): `test_gd_coverage` (15),
  `test_gd_duplicates` (7) and `test_gd_mutation` (32), 16 of them in the `unit` layer. They also skip locally without
  gdtoolkit, so they ran nowhere.

## Change

1. **Removed**, because the `static` job runs the same check on the same files: `ci.yml` step `check kit` runs
   `platforms/tools/check.sh --links` (`.github/workflows/ci.yml:61`), which runs `check_kit.py "$@"`
   (`platforms/tools/check.sh:22`) under `set -euo pipefail` and `CI=1` (`ci.yml:28`), on the checked-out tree the
   tests copied. `--links` only adds the `~/` link check (`check_kit.py:1287`), so it checks all the plain run does.
   - `test_check_kit_skill_use.CheckKitSkillUseTest.test_the_copy_passes`;
   - `test_just_modules.TemplatesNameKitRecipes.test_the_kit_passes`.
2. **Merged runs.** Each merged test asserts every expected FAIL line, each on a line of its own, and that no other
   FAIL line appears (before, most tests only asserted that their line was there):

   | Class | `check_kit.py` runs | Kept apart |
   |---|---|---|
   | `test_check_kit_references.CheckKitNestedReferencesTest` | 10 → 3 | none interact; two runs by rule (the flat checks at any depth, the index naming), plus `test_the_nested_references_pass`, kept because it also fails on a WARN line under `references/godot` or `references/java`, which the `static` job lets pass |
   | `test_check_kit_skill_use.CheckKitSkillUseTest` | 6 → 2 | the eval cases need pyyaml, the preloads do not |
   | `test_just_modules.TemplatesNameKitRecipes` | 6 → 1 | — |
   | `test_check_kit_readmes.CheckKitReadmesTest` | 5 → 3 (4 → 2 on Linux) | the bash 3 trap and the parse failure both edit `doctor.sh`, whose first error hides the next; the removed `CONTRIBUTING.md` breaks links elsewhere |
   | `test_hooks_context.CheckKitCatchesBrokenHooksTest` | 5 → 2 | a missing start hook hides every attribution case of its event |

3. **Synthetic fixtures** instead of kit wording: a synthetic description and link file for the session skill, two
   synthetic trigger eval cases, synthetic just modules and AGENTS and CI templates at the four paths `check_kit.py`
   § 14 reads; the checklist test asserts its marker, one line, the three git commands as code and the kit skill it
   names (the wording stays `check_kit.py`'s `CHECKLIST_WORDS` gate); the Godot template test asserts `--no-deps` on
   the second call and its `tee test-run.log`.
4. **gdtoolkit in CI**: the `unit`, `integration` and `red` jobs of `ci.yml` and the `integration` job of
   `ci-full.yml` install `platforms/kits/godot/requirements-gdtoolkit.txt` (`gdtoolkit==4.5.0`, the pin the Godot CI
   template gives projects). Under `CI=1` a test that parses GDScript fails without gdtoolkit instead of skipping, as
   a missing `just` or `gitleaks` does. The 4 `GodotTest` cases (Godot plus `KIT_GDUNIT4`) still skip.
   `red` installs it too: it runs a pull request's changed test modules under `CI=1`, so a change to a `test_gd_*`
   module would fail there without it. `test_kit_workflows` pins the install in each job that runs the unit or
   integration layer, and in `red`. The pin stays in one file, so the kit tests the gdtoolkit projects get; like
   `pyyaml` and `jsonschema`, the PyPI package is pinned by version, not by sha-256 (`--require-hashes` would need
   every dependency hashed).

## Proof

[FACT] On this branch, rebased on `6b5029b`, macOS, Python 3.12:

- `python3.12 -B platforms/ci/validations/check_kit.py`: `check: OK (1 plugins, 18 skills, 11 rules, 13 templates,
  14 readmes, 153 links, 57 hook cases, 19 shell scripts)`; `gen_index.py --check`: `plugin indexes are current`.
- The nine changed test modules whole (`run_tests.py <files>`): `Ran 153 tests`, `OK (skipped=58)`, the 54 gdtoolkit
  and 4 Godot skips.
- `run_tests.py --start platforms/ci/validations --changed-from origin/main`: `Ran 272 tests`, `OK (skipped=59)`.
- The same with `CI=1` and a throwaway venv holding `gdtoolkit==4.5.0`, `pyyaml` and `jsonschema`: `Ran 272 tests`,
  `OK (skipped=5)` (4 `GodotTest`, 1 `SPEC_TRACE_CORPUS`), so the 54 GDScript tool tests ran and passed. The three
  `test_gd_*` modules with `CI=1` and no gdtoolkit: `FAILED (failures=54, skipped=4)`, each failure
  `gdtoolkit is not installed (CI=1 makes it required: ...)`; without `CI`: 54 skips.
- A merged test can fail: with `check_kit.py`'s `Not for` check disabled, the readmes run fails on the missing line
  (`0 != 1`) and on the FAIL count (`2 != 3`).
- `actionlint` 1.7.12 and `zizmor --offline` 1.32.0 on `ci.yml` and `ci-full.yml`: no findings (zizmor's one
  suppressed finding is the base's).

## Measured

[FACT] Each class run serially on its own (`unittest`, Python 3.12, macOS), the base (`87faade`) and this branch,
then on that base, side by side so both saw the same load (load average 14–37, other sessions running), with every
`check_kit.py` subprocess counted:

| Class | Tests | `check_kit.py` runs | Seconds |
|---|---|---|---|
| `CheckKitNestedReferencesTest` | 10 → 3 | 10 → 3 | 208.2 → 50.9 + one unmeasured run |
| `CheckKitSkillUseTest` | 6 → 2 | 6 → 2 | 120.4 → 46.9 |
| `TemplatesNameKitRecipes` | 6 → 1 | 6 → 1 | 132.9 → 26.3 |
| `CheckKitReadmesTest` | 5 → 3 | 5 → 3 | 269.4 → 162.4 |
| `CheckKitCatchesBrokenHooksTest` | 5 → 2 | 5 → 2 | 146.5 → 83.8 |
| Total | 32 → 11 | 32 → 11 | 877.4 → 370.3 + one unmeasured run |

The 21 fewer tests are the two removed above and 19 merged into the runs that keep their assertions. In CI the
integration shards run these tests in parallel, so the wall time of a shard drops less than the sum.

## What would prove it wrong

A `check_kit.py` regression that one of the removed or merged tests caught and the new ones miss: a check whose FAIL
line a merged mutation hides,.

## History

- 2026-11-16: confirmed (owner, "Sim, comece a parte A").
