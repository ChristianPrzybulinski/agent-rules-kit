---
id: KIT-100
title: "The FEAT-only flow: a FEAT with no NEED, no REQ and no task rows, its status from its PR"
status: done
confirmed: "2026-11-16 (owner, kit chat: \"Sim, faça\" on E § 17, backlog G7)"
issue: "#342"
pr: "#365"
---

# KIT-100 — The FEAT-only flow: a FEAT with no NEED, no REQ and no task rows, its status from its PR

## Problem and evidence

[FACT] The game-profile evaluation (`KIT-GAME-PROFILE-EVALUATION-2026-11-16.md` in the owner's workspace, "E"),
§§ 10 and 17.3, backlog G7: a tool repository (the kit itself) runs FEATs without NEEDs, REQs or journeys. KIT-088
added the keys (`sdd.flow`, `task_table`, `record_when`, `id_prefix.feature`, the `tooling` preset), but nothing read
them:

1. `check_spec.py` required `requirements` on every FEAT and an id `FEAT-nnn`; `spec_trace.py` loaded only
   `features/FEAT-*.md`; a FEAT reached `delivered` only through `validate`/`deliver`, which need task rows.
2. `sdd-clarify` wrote REQs and `sdd-tasks` wrote rows whatever the flow; `sdd-check` C1 blocked a FEAT with no REQ.
3. Review note of #348 (KIT-089): for `kind: tooling`, `init-spec.sh` copied `spec-index-business.md`, whose explicit
   `sdd:` block (`needs: true`, nine Plan sections, `pr_unit: task`, `release: merge`) overrides the tooling preset.

## Change

- `plugins/guardrails/templates/spec-feature-lite.md` (new): Problem and evidence, Scope, Out of scope, Acceptance
  criteria with a `Proof` column and no `Proves`, Plan (`Tests`, `Risks`), Decisions, History; frontmatter with no
  `requirements` and with `issue` and `pr`.
- `plugins/guardrails/templates/spec-index-tooling.md` (new): a one-paragraph index with Features and Decisions
  tables and no `sdd:` block. `init-spec.sh` copies it for `project.kind: tooling`; the folders follow the resolved
  `sdd.flow`, not the kind (only `features/`, `decisions/` and `debts/` under `feat-only`, so a business project on
  `feat-only` and a tooling one back on `full` each get their flow's folders); it now resolves the profile before
  creating any folder.
- `check_spec.py`, in new functions (`flow_params`, `apply_flow`, `check_closure`) with two call-site lines: reads
  `sdd.flow` and `sdd.id_prefix.feature` through `load_params` (so `.ai-kit.yaml` and the kind preset count). The FEAT
  id is `<prefix>-nnn`. Under `feat-only` a FEAT needs no `requirements`, may carry `issue` and `pr` (`#N`,
  `OWNER/NAME#N` or empty), and `delivered` is also proved by the line `- <date> pr: delivered (<repo>#N merged)`. A
  refused profile key stays profile.py's finding and leaves the full flow. The full flow with the `FEAT` prefix uses
  the schema and the structural rule exactly as before.
- `spec_trace.py`, in new functions (`feat_glob`, `feat_prs`, `pr_feat_status`) with three call-site lines: FEAT
  files are `<prefix>-*.md`; under `feat-only`, `sync-status` reads the PR the `pr` field names (one `gh api
  repos/<repo>/pulls/<n>` call), else the PRs whose body closes the FEAT's `issue` (the listing it already makes), and
  moves a proposed or planned FEAT to `in-progress` on an open PR and an open FEAT to `delivered` on a merged one,
  each with its `pr:` History line; a PR closed unmerged warns; delivered, cancelled and non-FEAT statuses (a
  project's older records) are never rewritten. A `pr` or `issue` that is not `#N` or `OWNER/NAME#N` in ASCII digits
  (the field pattern check_spec.py's `ITEM_REF` uses), or that names a repository outside the backlog, its earlier
  names and PR repositories, never reaches `gh`: it prints `WARN <fid>: ...; status not synced` and the sync goes on.
- Versioned FEATs (KIT-096): a lite FEAT may carry `## Versions`; its blocks need no REQ in their Scope, the FEAT's `pr`
  names the open block's PR, and a merged PR delivers the FEAT and sets the last block's `Status:` (sync-status writes
  both), which check_spec.py accepts. Each new block names its own item in `issue`/`pr`.
- Skills, each reading the key, never `project.kind`: `sdd-clarify` does not run under `flow: feat-only`; `sdd-tasks`
  does not run under `task_table: false` (the schema names `sdd-tasks` as that key's reader; the tooling preset sets it
  with `feat-only`); `sdd-check` runs only the full scope, C1 and C8 against criteria and proofs, without the REQ rows;
  `sdd-plan` writes the lite template under `record_when`; `sdd-review` does not run (the PR review is the closure);
  `sdd-constitution` names the tooling template and folders.
- `check_kit.py` SPEC_MAP gains `spec-index-tooling`; `INDEX.md` regenerated; CHANGELOG.

## Proof

[FACT] On branch `feat/kit-100-feat-only-flow`, macOS:

- Red first: the new `test_check_spec_feat_only.py` (12 tests), `test_spec_trace_feat_only.py` (10) and two new
  `test_init_spec.py` tests: 16 of 28 failed before the change (the 12 passing ones are the full-flow guards), all
  pass after, under `python3.12` and `/usr/bin/python3` 3.9.6.
- Byte for byte: `check_spec.py` (full and `--params`, `python3.12` and `/usr/bin/python3`) and `spec_trace.py
  check`, `status`, `lint`, `enablers` on `platforms/ci/fixtures/consumer/docs/spec` and on a copy of Stratics'
  `docs/spec` (97 FEATs) print the same output and exit code with `origin/main`'s tools and with this branch's: 16
  outputs identical.
- `bash platforms/tools/check.sh`: `check: OK (1 plugins, 18 skills, 11 rules, 18 templates, 15 readmes, 170 links,
  65 hook cases, 18 shell scripts)`, indexes current, no new WARN; `check.sh --links` OK; `shellcheck -x` and
  `bash -n` (3.2) on `init-spec.sh` clean.
- `python3.12 platforms/tools/run_tests.py --layer unit,contract`: `Ran 311 tests`, `OK (skipped=16)` (gdtoolkit);
  `--layer integration --changed-from origin/main`: `Ran 658 tests`, `OK (skipped=1)` (a non-UTF-8 file name).
- `/usr/bin/python3` 3.9.6 on the touched test modules: `Ran 161 tests`, OK.
- Not verified: the edited skill text on a real tooling project (no eval case covers `sdd-clarify`, `sdd-tasks`,
  `sdd-plan`, `sdd-review` or `sdd-check`; evals not run), and `sync-status` against the live GitHub API (mocked).

After the review (READY at 80d878a), `origin/main` 14c2109 (KIT-094, KIT-096, KIT-099) merged in: the conflicts
(`docs/features/README.md`, `sdd-tasks`) resolved by hand; the follow-ups above (allowlist warning, ASCII item
pattern, folders by flow, versioned lite FEATs): 3 of the 4 new tests failed before the fix, all pass after; the versioned one passed as
merged, so it pins the coexistence rather than proving a fix. Byte for byte
again against 14c2109's tools: 16 outputs identical. `check.sh` and `--links`: `check: OK (1 plugins, 18 skills, 11
rules, 18 templates, 15 readmes, 174 links, 65 hook cases, 18 shell scripts)`; `--layer unit,contract`: `Ran 311
tests`, `OK (skipped=16)`; `--layer integration --changed-from origin/main`: `Ran 758 tests`, `OK (skipped=1)`;
`/usr/bin/python3` on the three feat-only test modules: `Ran 32 tests`, OK; `shellcheck -x` on `init-spec.sh` clean.

## History

- 2026-11-16: confirmed (owner, kit chat; issue #342).
- 2026-11-17: implemented on `feat/kit-100-feat-only-flow`.
- 2026-11-17: review follow-ups and `origin/main` 14c2109 merged in.
- 2026-11-22: status done (#342 closed by #365; #439).
- 2026-11-22 amend (#451): sync-status (the spec.md Status cell), impact and lint take the FEAT id from sdd.id_prefix.feature, as feat_glob already did; found on #449, where KIT-116's index row stayed in-progress.
