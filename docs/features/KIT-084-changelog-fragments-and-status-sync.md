---
id: KIT-084
title: "Ship the changelog.d consolidator, the spec status-sync workflow and the gitleaks action from the kit"
status: in-progress
confirmed: "2026-11-16 (owner, chat of the kit session: \"Sim, abra as duas\"; the gitleaks action added the same day: \"usar do kit\")"
issue: "#319"
pr: ""
---

# KIT-084 — Ship the changelog.d consolidator, the spec status-sync workflow and the gitleaks action from the kit

A comparison of a consumer project's process files with kit 14.0.0, after its KIT-081 migration, found generic tools
that lived only in that project. Following KIT-081, a project now runs them from the installed kit, and nothing is
copied into it.

## Problem and evidence

[FACT] Read on `origin/main` `be62ae9` and in the consumer's sources, 2026-11-16:

1. **No consolidator.** `sdd-implement/references/task-pr.md:11` asked for "a `changelog.d/` fragment when the repo uses
   one", and the kit shipped no tool to validate or consolidate one. `pr_gates.py:55` (`FRAGMENT_RE`) matches a
   fragment's file name only; neither it nor `row_checks.py` parses a fragment's body, so there was no parser to share.
   The consumer's consolidator (97 lines, stdlib) had two silent losses, both reproduced by the new tests on a verbatim
   port: a `changelog.d/*.md` whose name has no known type was deleted without its bullets moving
   (`test_a_file_without_a_fragment_name_is_named_not_deleted`: `SystemExit not raised`), and a `## [Unreleased]`
   heading last in the file with no newline after it took the bullets nowhere while the fragments were deleted
   (`test_a_changelog_without_an_unreleased_line_is_named_and_nothing_moves`: `SystemExit not raised`); without the
   heading it raised `ValueError: substring not found`.
2. **The status-sync pull request ran from a project workflow.** `spec_trace.py sync-status --write` is the kit's; the
   workflow that runs it and opens the pull request, and its body file, lived in the project.
3. **No cross-repository secret scan.** The `gitleaks.yml` template is a workflow to copy: GitHub calls a reusable
   workflow across repositories only from a repository's `.github/workflows/`, so a project could not call it from the
   kit and inlined the scan to keep one billed job per run.

## Change

1. `platforms/ci/validations/changelog_fragments.py`, beside `spec_trace.py` and `pr_gates.py` (a project CI tool run
   from `$AI_KIT_DIR`, while `platforms/tools/` holds the kit's machine lifecycle): `--repo-dir DIR` consolidates,
   `--check` writes nothing. `parse_fragment` keeps the consumer's rules and messages; a misnamed `*.md`, a missing
   `CHANGELOG.md` and a `CHANGELOG.md` without a `## [Unreleased]` line are named before any write, and with no fragment
   nothing is read or written. Tests: `test_changelog_fragments.py` (the consumer's 12 tests ported, 9 new).
2. `platforms/kits/just/docs.just` gains `changelog *ARGS`, which runs the installed kit's tool from the repository root.
3. The templates `platforms/kits/github/workflows/changelog-consolidate.yml` and `spec-status-sync.yml`: dispatch only
   (a comment shows the `schedule:` lines), the spec-tools action at the templates' pin with `checks: none`, the kit tool
   from `$AI_KIT_DIR`, then one pull request on a fixed branch, opened or refreshed only when the tool changed a file,
   never merged, with an inline body. The secret `PR_BOT_TOKEN` (permissions in `platforms/kits/github/README.md`)
   reaches git through a credential helper in the one step that pushes; the checkout keeps no credential. Timeouts from
   the consumer's green runs: 46 s and 441 s, so 5 and 25 minutes. Tests: `test_pr_bot_templates.py`.
4. `platforms/ci/actions/gitleaks/` (`action.yml`, README): the gitleaks CLI at the version and sha-256 of the kit's own
   `.github/workflows/gitleaks.yml`, a `config` input, a pull request's commits (`base..head`, an error when the base is
   not in the checkout) or the whole history on any other event. The `gitleaks.yml` template now calls it in its one
   job, so a pull request scans its own commits instead of the whole history; `scan.md` follows. The kit's own
   `gitleaks.yml` keeps its inline steps (a required check whose `uses:` lines the SHA-pin test reads); a test holds the
   two pins equal. Dependabot watches the folder; zizmor's `platforms/ci/actions/*/action.yml` already reads it.
5. Docs: `platforms/kits/github/README.md`, `platforms/ci/README.md`, `platforms/kits/just/README.md`,
   `docs/projects.md`, `task-pr.md`, `scan.md`, `.github/CONTRIBUTING.md` (Dependabot), the CHANGELOG.

## Proof

[FACT] On this branch, macOS, Python 3.12:

- Red: the new test module before the tool existed: `FileNotFoundError: ... changelog_fragments.py`; on a verbatim
  port of the consumer's tool, 12 of 21 tests passed and 9 failed: the misnamed file and the heading at the end
  (`SystemExit not raised`), no heading (`ValueError: substring not found`), no `CHANGELOG.md` (`FileNotFoundError`)
  and the `--check` tests (`no attribute 'check'`, exit 2 for the unknown flag). `test_pr_bot_templates` (8 of 8) and
  `test_gitleaks_template` (12 of 13; the template's triggers were already right) failed before the templates and the
  action existed (`FileNotFoundError`, the template's `0 != 1` action steps, the Dependabot folder missing); `test_just_modules` failed with
  ``justfile does not contain recipe `changelog` ``.
- Green: `test_changelog_fragments` 21, `test_pr_bot_templates` 8, `test_gitleaks_template` 13, `test_kit_workflows`
  35 (its contract classes), `test_just_modules` 27, `test_sync_dev_standards` 12 (its docs recipe set gains `changelog`), all OK;
  `run_tests.py --layer unit,contract`: `Ran 199 tests`, `OK (skipped=16)` (gdtoolkit);
  `run_tests.py --layer integration --changed-from origin/main`: `Ran 107 tests`, `OK (skipped=1)` (a non-UTF-8 file name
  this file system refuses); the first run failed `test_sync_dev_standards` on the new recipe, fixed above.
- `check.sh` with `python3` at 3.12: `check: OK (1 plugins, 18 skills, 11 rules, 13 templates, 15 readmes, 156 links, 57 hook
  cases, 18 shell scripts)`, `plugin indexes are current`, both `claude plugin validate` passed; actionlint 1.7.12 on every workflow and template: clean;
  `zizmor --offline` 1.32.0 on the workflows, templates and both actions: no findings (the pedantic persona adds only
  the known anonymous-job and concurrency notes); ShellCheck and `/bin/bash -n` (3.2) on each new `run:` step: clean;
  the credential helper answered `git credential fill` with the token from the environment.
- Not run here: the templates and the action on a GitHub runner, zizmor's online audits, the functional layer and the
  integration classes the change does not select (CI's jobs), and the evals for the two edited references.

## What would prove it wrong

- A runner whose `git` ignores `-c credential.helper=` (an empty value resets the list since git 2.9) would push without
  the token and fail; the helper was tested with `git credential fill`, not on a GitHub runner.
- Every template pins the spec-tools action at v14.0.0, which has neither `changelog_fragments.py` nor the gitleaks
  action: until a release that ships them is pinned, the changelog step fails with "can't open file" and the gitleaks
  template at its `uses:` line. The kit's Dependabot moves the pins after that release.

## History

- 2026-11-16: confirmed (owner, "Sim, abra as duas"); the gitleaks action added to the scope ("usar do kit").
