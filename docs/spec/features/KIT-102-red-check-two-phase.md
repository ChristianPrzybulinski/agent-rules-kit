---
id: KIT-102
title: "Split the red check into a plan and a judge of given sides"
status: planned
issue: "#378"
pr: ""
created: "2026-11-17"
updated: "2026-11-17"
---

# KIT-102 — Split the red check into a plan and a judge of given sides

## Problem and evidence

[FACT] The Stratics review loop (dev-game-studio/review-loop) runs `platforms/tools/review_checks.py red` inside a
candidate sandbox that denies the Docker socket (`loop_gate_run.py`, `_red_fixture_run`, stratics#4457). A test that
needs a Postgres container must run in a separate sealed VM that the loop engine launches, one job per run. `red`
makes both worktrees, runs base and head and judges them in one process (`red()` in `review_checks.py`), so it cannot
hand the run to that VM. The owner chose to split the check, with the verdict logic kept only in the kit
(dev-game-studio/stratics#4670 item 6, option B; follow-up dev-game-studio/stratics#4687).

## Scope

- `platforms/tools/review_checks.py`: `red --plan OUT.json` writes the selection (`status`, `base`, `head`,
  `test_files`, `classes`, `command`, `cwd`, `run_folder`, `junit`) and runs nothing; `red --sides-from DIR` reads
  `DIR/base/` and `DIR/head/` (`exit_code`, `output.txt`, optional `reports/`) and gives the verdict; the one-process
  run and `--sides-from` share `red_select` and `red_judge`, so the verdict logic has one copy. Without either flag the
  check is unchanged.
- `platforms/ci/validations/test_review_checks.py`: class `RedTwoPhaseTest`.
- `platforms/tools/README.md`: the `review_checks.py` row names both flags.

## Out of scope

- The loop engine's VM job, which runs the plan's command and writes the sides folder: dev-game-studio/review-loop,
  stratics#4687.
- Several gates `red` entries claiming the PR's tests in one two-phase run: the folder holds one run per side, so both
  flags exit 2 there.

## Acceptance criteria

| ID | Given | When | Then | Proof |
|---|---|---|---|---|
| CA-1 | a PR with test and code changes | `red --plan OUT.json` | OUT.json holds the test files, the `{classes}` string, the filled command and the run folder of a leading `cd`; no command ran, no worktree was made; exit 0 | `python3 platforms/tools/run_tests.py platforms/ci/validations/test_review_checks.py` |
| CA-2 | a PR with no test file, or only tests | `red --plan OUT.json` | exit 1 (NONE) or 0 (EXEMPT), `status` says which, `command` is null | `python3 platforms/tools/run_tests.py platforms/ci/validations/test_review_checks.py` |
| CA-3 | sides a runner wrote for each verdict class | `red --sides-from DIR` | the class, the lines and the exit code (0, 1, 2 or 3) of the one-process run; no command ran, no worktree was made | `python3 platforms/tools/run_tests.py platforms/ci/validations/test_review_checks.py` |
| CA-4 | a side folder missing a file, or an `exit_code` that is no integer; or both flags | `red --sides-from DIR` | exit 2, naming the side or the file; no verdict | `python3 platforms/tools/run_tests.py platforms/ci/validations/test_review_checks.py` |

## Plan

### Tests

`RedTwoPhaseTest` builds throwaway repositories as `RedTest` does. A test helper plays the engine: it reads the plan,
runs its command in worktrees of base (with the PR's test files) and head, and writes the sides folder. Each verdict
class goes through `--sides-from`; one test feeds the same PRs to the one-process run and to the two phases and
compares the `red: ` lines and exit codes; one writes the folder by hand, so the format alone carries the verdict.

### Risks

- The engine's output differs from `run_group`'s (stdout then stderr): the verdict reads the same patterns in either
  order, but an excerpt may read differently.
- A runner that writes a non-JUnit XML file into `reports/`: the judge reads every XML file there, and one that does
  not parse is exit 2.

## Decisions

- 2026-11-17 (#378): chose to read every XML file under `reports/` over the `--junit` globs, because the runner
  copies only the reports the plan's `junit` names, relative to its own tree.
- 2026-11-17 (#378): chose exit 2 for several gates `red` entries over a combined shell command, because a side's one
  exit code and output would hide which group ran no test.

## History

- 2026-11-17 plan: created from the request (dev-game-studio/stratics#4687, issue #378).
