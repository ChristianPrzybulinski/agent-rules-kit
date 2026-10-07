---
id: KIT-005
title: "Gates prove nothing in a sparse or partial checkout"
status: done
confirmed: "2026-10-07 (owner, chat of the Stratics E5' batch session)"
issue: "#77"
pr: ""
---

# KIT-005 — Gates prove nothing in a sparse or partial checkout

## Problem and evidence

[FACT] On 2026-10-07 the Stratics architect session reviewed docs PRs in sparse worktrees (`git worktree add
--no-checkout` plus a cone sparse checkout, the recipe that keeps a stratics-docs worktree fast). Reproduction on
stratics-docs `origin/main` with the cone `docs/spec .github platform/review-loop platform/tools/spec-trace
platform/tools/row-lint platform/scripts changelog.d`: `bash platform/scripts/dev.sh lint` printed `spec: OK` and
`spec-trace: OK`, then `can't open file '…/platform/tools/protocol-check/check.py'`, and exited 2. The script runs
under `set -euo pipefail`, so every later step was skipped, the `doc-structure` check among them.

[FACT] That check was red on stratics-docs `main` after two reviewed PRs: `platform/infra/backup/` had no README
(stratics-docs#607), and `platform/tools/protocol-gen/README.md` did not start with a `# ` title (#610). Both
failures were confirmed on the base `681802287` and fixed as FEAT-053 T9.

[HYPOTHESIS] The two reviews missed it because their lint run stopped early in a sparse worktree. The early stop is
reproduced; what those two runs printed was not kept.

## Change

- `plugins/quality-core/skills/validate-implementation/SKILL.md`, § 3 Run canonical gates, gains: "Run the gates in
  a complete checkout of the repository. A sparse or partial worktree is for editing: a gate that stops there on a
  missing path (`can't open file`, `No such file`) is a failed run, never a pass, and under `set -e` it skips every
  later gate — rerun from a full checkout before the verdict."

## Proof

`bash platforms/tools/check.sh`; `python3 platforms/ci/validations/check_kit.py --links`.

## History

- 2026-10-07: confirmed and done (owner, chat; the Stratics E5' batch report).
