---
id: KIT-075
title: "sdd.needs: false runs the front chain without NEED files, a doing row moves the FEAT, and review_checks and pr_gates close the #246 review gaps"
status: confirmed
confirmed: "2026-11-16 (coordinator under the owner's full autonomy for the night, chat of the rules-and-skills review session: the 13.0.0 follow-ups #237, #247, #248-#255)"
issue: "#284"
pr: "#285"
---

# KIT-075 — sdd.needs: false runs the front chain without NEED files, a doing row moves the FEAT, and review_checks and pr_gates close the #246 review gaps

## Problem and evidence

[FACT] Ten follow-ups stay open before 13.0.0 (kit `40fa0d8`):

- #237: `sdd.needs` is validated and documented (KIT-067), but no step reads it; `sdd-parameters.md` says "not wired
  yet (#237)".
- #247: `spec_trace.py derived_status` returns `in-progress` only when a row is `done`, so a FEAT whose rows are
  `todo`/`doing` stays `planned` while its work runs.
- #248-#255, found by the reviews of #246: `dod` counts no assertion for a rename out of the runner's discovery
  pattern (`tests/test_add.py` → `tests/test_add.py.off`); `feat-proofs` reads in-repo rules from `HEAD`; FF, NEL or
  U+2028 inside a task row drops the row; `pr_gates.sections`, `parse_proof` and `widened_paths` split on
  `str.splitlines()`; `protected_paths` given as a string is globbed per character; a 300-character path component
  and a PR test under a base file crash with exit 2; a CR-only test file is one diff line, so a dropped assertion
  passes `dod`; an import error and `red --timeout 0` exit 1.

## Change

- #237, `sdd.needs: false` [DECISION] (the PR #236 review's minimal proposal, taken under owner-review autonomy):
  `sdd-intake` is skipped; `sdd-specify` decides and describes in the conversation; `sdd-plan` writes the Request
  quote, Triage, desired outcome, Situations and scope into the FEAT's Problem section; `sdd-clarify` writes REQs with
  `source: request YYYY-MM-DD S<n>`, which land in the change that creates their FEAT; `sdd-check` runs no functional
  scope and reads the FEAT's Problem section where it read the NEED. `check_spec.py` fails a NEED file (rule
  `needs-off`) and a REQ with no FEAT. `sdd-parameters.md` names the readers instead of "not wired yet".
- #247: `spec_trace.py derived_status` moves a FEAT to `in-progress` on a `doing` or `done` row (`ROW_STARTED`), and
  `status --write` adds `status: <old> -> in-progress (<rows>)` to History. `sdd-process.md` and the
  `spec-feature.md` comment name the row states.
- `platforms/ci/validations/pr_gates.py`: `body_lines` splits a body only on CRLF, CR and LF, used by `sections` and
  `parse_proof` (#251); `config_errors(config, required)` checks each known key's type, and `main` exits 2 naming
  the key (#252).
- `platforms/tools/review_checks.py`: `dod --gates` takes the runners' discovery patterns from the `red` globs (#248);
  `feat_rows` splits on `\n` only (#250); `widened_paths` uses `body_lines` (#251); `gates_config` refuses a wrong
  type naming the key (#252); a path the file system cannot check and a PR test that cannot be placed on base are
  findings (#253); `dod` counts assertions per CR line (#254); a missing `pr_gates` and a `--timeout` below 1 exit 2
  (#255). `feat-proofs` keeps reading `HEAD` without `--base` (#249): it runs on `main` after the merge, where HEAD
  is the trusted ref; the `delivery-steps.md` sentence that says so, with the `dod --gates`, CR-count and exit-2
  wording, goes in through KIT-077, which owns that file.
- Docs: the five front-chain skills, `sdd-parameters.md`, `sdd-process.md`, `spec-feature.md`,
  `platforms/tools/README.md`, CHANGELOG.

## Proof

- Tests first: the new tests in `test_review_checks.py`, `test_pr_gates_inputs.py` (new), `test_spec_trace.py` and
  `test_check_spec.py` fail on `40fa0d8` and pass with the fix (`review_checks.py red`, recorded in the PR); the #249
  test pins the kept behaviour and passes on both.
- Locally, the modules that cover the changed files and `check_kit.py`; CI runs the rest (`ci`, `workflow-lint`,
  `gitleaks`, `codeql (python)`, `codeql (actions)`).

## History

- 2026-11-16: confirmed (coordinator, under the owner's autonomy for the night).
