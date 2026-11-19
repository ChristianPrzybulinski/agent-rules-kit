---
description: PR-gates mode of skill review — the no-model pr_gates.py contract, scope and proof gates, its JSON config and how to run it.
kind: detail
---

# PR gates

The no-model PR contract gates as a CI check or a local report: `platforms/ci/validations/pr_gates.py`, deployed by `platforms/kits/github/workflows/pr-contract.yml`. Reads through the GitHub REST API — `GH_TOKEN` must read the PR's repo, the backlog repo's issues and the head's checks (in CI a PAT; a PR repo's GITHUB_TOKEN cannot read the backlog's issues).

## 1. Gates config

One JSON file describes the project (the module docstring lists every key): `owner`, `backlog_repo`, `repos` (each with optional `require_fragment`), `protected_paths` (label → globs), `generated_neighbours`, `proof_allowlist`, `expected_red_checks`, optional `review_context`. Keep it beside the script in the backlog repository, on a protected ref — the workflow checks out that ref, never the PR head, because the job holds the token.

## 2. Run

- `python3 pr_gates.py --config <gates.json> --repo <name> --pr <n>` — Markdown report on stdout, exit 1 on failure.
- `python3 pr_gates.py proof-commands --config <gates.json> --repo <name> --pr <n>` — the PR's allowlisted `proof` block commands, one per line, for the caller's `proof` job.
- A body without `Closes` or `Refs <owner>/<backlog>#N` is a `no-task` PR: the task gates report `skip` and only the CI state is evaluated — architect PRs pass.

## 3. Gates

Issue link (`Closes` for legacy tasks, `Refs` for a FEAT), proof block, owned-areas scope, protected paths need their label, no overlap with other open PRs, changelog fragment when required, proof commands inside the allowlist, CI green — pending CI is reported, not failed.

For a canonical FEAT issue, the approved table is mirrored under `## Tasks`; a PR selects ids under `## Task rows` (`T1, T2`), before the required `## Proof` heading. Its final `Refs` line stays outside the row-selection section. The gate validates only those rows' Files, rejects missing or unknown ids and never uses the whole issue Files union. Keep repository-qualified Files as the gate already requires. Imported callers pass that section as `evaluate_gates(..., task_rows=...)`; a mirrored table without a selection fails closed. The legacy gate key `contract: Closes link` is retained for consumers and accepts both link forms.

## Rules

- Never run the gates from a PR head — checkout stays on the protected ref; never execute the proof commands here — the caller's `proof` job runs them; never weaken the allowlist to make a PR pass.

Done when: the report prints **PASSED** (or `pending` only on CI) and no gate failed.
