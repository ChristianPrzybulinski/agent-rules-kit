---
id: KIT-073
title: "spec_trace.py gains sync-status, the journey checklist and the spec.md index check, and row_checks.py checks task rows a-k from the sdd: block"
status: confirmed
confirmed: "2026-11-15 (owner, chat of the rules-and-skills review session: a consumer's generic repository tools become kit standards in 13.0.0)"
issue: "#259"
pr: ""
---

# KIT-073 — spec_trace.py gains sync-status, the journey checklist and the spec.md index check, and row_checks.py checks task rows a-k from the sdd: block

## Problem and evidence

[FACT] A consumer project kept two tools of its own beside the kit's spec validators (comparison 2026-11-15, consumer
`82ed724e4`, kit `4f035d1`):

- Its `spec_trace.py` (1039 lines) diverged from the kit copy (944 lines) both ways. Only the project's had
  `sync-status` (row Status from GitHub issues and PRs through `gh`), the journey `checklist J-NN` and the `spec.md`
  index check; both were coupled to project modules, and the project's CI ran its own copy.
- Its row linter checked task rows before the cut with eleven rules (a–k). The kit stated those checks in prose
  (`sdd-tasks/references/row-checks.md`) and enforced only the dependency part in `check_spec.py`.
- `command_allowed` existed three times: the kit's `pr_gates.py` and two consumer copies, one with a working-directory
  sandbox the kit's lacked.

## Change

- `platforms/ci/validations/spec_trace.py`: `sync-status [--write] [--backlog OWNER/REPO]` (only with `sdd.tracker:
  github`; `gh api` REST GETs of the backlog issues and of each PR repository's pulls; row Status per `task-issue.md`
  § States, `todo`/`doing`/`blocked`/`done`/`cancelled`; a `done` row stays `done`; FEAT status by KIT-069's
  `derived_status`, never `validated` or `delivered`; with `--write` the FEAT files, `traceability.md` and the `spec.md`
  Status cells and sync block), `checklist J-NN … [--out FILE] [--force]`, the `spec.md` index check behind
  `sdd.spec_index`, journey test paths under `sdd.components`. Every subcommand's spec argument is optional (default
  `docs/spec`). The release checklist with fixed runbooks stays in the project.
- `platforms/ci/validations/row_checks.py` (new): `check FEAT-nnn … | --all | --changed BASE HEAD [--all-rows]
  [--strict]`, rules a–k read from `components`, `row_checks` (`gates`, `tests`, `assets`, `protocol`, `artifacts`,
  `visual`) and `visual_approval`; `sdd.row_check: null` now means this command.
- `platforms/ci/validations/pr_gates.py`: one `command_allowed(cmd, allowlist, cwd=None, var_depths=None)` with the
  optional working-directory sandbox (`proof_var_depths`) and the refusal of `! git diff` without `--quiet` or
  `--exit-code`; `row_checks.py` imports it.
- `platforms/ci/validations/check_spec.py`: `load_params(spec_dir, schemas_dir)` for the tools that read the block.
- `platforms/ci/schemas/spec.schema.json`, `plugins/guardrails/templates/spec-index.md`: the keys `components`,
  `spec_index`, `github`, `row_checks` with their defaults.
- `platforms/tools/sync-project.sh`: `kit_files()` vendors `row_checks.py` and `pr_gates.py` into `.github/spec-lint/`;
  `--check` reports a missing or edited copy.
- Docs: `sdd-tasks/SKILL.md` (row-check default), `sdd-tasks/references/row-checks.md` (§ Automated rules),
  `sdd-constitution/references/sdd-parameters.md`, `platforms/ci/README.md`, `platforms/tools/README.md`, CHANGELOG.
- Tests (neutral fixtures, `gh` canned, no network): `test_row_checks.py`, `test_row_checks_contract.py`,
  `test_spec_trace_sync_status.py`, `test_spec_trace_checklist.py`, `test_pr_gates_command.py`,
  `test_sync_project_spec_tools.py`; `test_check_spec.py` gains the new defaults.

## Proof

- The kit gates: `bash platforms/tools/check.sh`, `CI=1 bash platforms/tools/check.sh`, `bash platforms/tools/smoke.sh`,
  `python3 platforms/ci/validations/check_kit.py --links`, `python3 -B -m unittest discover -s platforms/ci/validations
  -p "test_*.py"`.
- Falsifier: the kit tools and the consumer's on the consumer tree (`82ed724e4`) with a mirroring `sdd:` block. Row
  checks on the 342 open rows: every one of the consumer's 11 findings, plus 39 header FAILs asking for the KIT-068
  columns. On all 1846 rows, each difference has a reason: legacy headers and Status words (rule a), a retired proof
  form the kit never had (16 j WARNs on `done` rows), per-path and listed-neighbour d WARNs (KIT-068: neighbours
  implicit), one pre-monorepo mixed-root row (b). `spec_trace.py` `check`, `generate`, `status`, `impact`, `checklist`
  and the index check match except headings; `sync-status` (79 read-only `gh api` GETs, replayed identically to both)
  differs only by the KIT-068 row words, `cancelled` for not-planned issues, the kit bundle-title form, and KIT-069's
  FEAT derivation. One defect found and fixed: a `done` row whose issue was closed as not planned turned `cancelled`.

## History

- 2026-11-15: confirmed (owner, through the coordinating session).
- 2026-11-15: implemented; falsifier differences listed in the PR.
