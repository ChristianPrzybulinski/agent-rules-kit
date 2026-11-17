---
id: KIT-097
title: "Duplicate checks C20-C24: one rule, process, contract and use case in one place"
status: in-progress
confirmed: "2026-11-16 (owner, kit chat: \"Sim, faça\" on E § 17, backlog G11)"
issue: "#339"
pr: ""
---

# KIT-097 — Duplicate checks C20-C24: one rule, process, contract and use case in one place

## Problem and evidence

[FACT] The owner's game-profile evaluation (`KIT-GAME-PROFILE-EVALUATION-2026-11-16.md` in the owner's workspace,
"E" below) § 13: "precisamos ter essas revisões nas skills, pra garantir que uma regra não seja duplicada, uma feat não
exista 2 ou 3 vezes". § 13.1, measured on Stratics `origin/main` `8d7495894`: 80 of the 657 REQs that FEATs list are
listed by more than one FEAT, 3 of them by more than one open FEAT; text-level REQ duplication is rare (one title pair
above 0.9 similarity, a legitimate one), so real duplicates need judgment. Only the NEED-level search existed
(`sdd-specify`, "a NEED with the same request"). The owner accepted the rows C20-C24 and a `spec_trace.py similar`
candidate list (E § 17.3 G11, § 17.6).

## Change

- `spec_trace.py` (new functions `similar_words`, `statement_parts`, `similar_pairs`, `c20_candidates`,
  `c21_findings`, `c22_candidates`, `c23_candidates`, `c24_findings`, `similar_command`; call sites: one subparser and
  one dispatch line in `main`): new command `similar [SPEC]`. Words compare after one deterministic normalization:
  casefold, claim tags and punctuation removed, stop words dropped, order ignored (`not` and `no` count). One line per
  pair, then `similar: N findings (C21, C24), M candidates (C20, C22, C23); …`.
  - Findings (mechanical), exit 1: C21 a contract id two ENBs provide; C24 a REQ in two open blocks, where an open
    block is a versioned FEAT's last block (its Scope REQs) or a FEAT without `## Versions` (its `requirements`),
    while not validated, delivered or cancelled.
  - Candidates (judgment), exit 0: C20 two REQs with the same actor, trigger and result (a statement in the template's
    form "The system must <result>, when <trigger>, for <actor>."), else the same statement words, else the same
    title words; C22 two processes with the same Trigger words and an Actors line in common; C23 two FEATs with the
    same `- Use case:` words or a process step both declare (`declared_steps`, KIT-096).
  - Retired REQs and processes and cancelled FEATs take no part. `check`, `generate` and every other command are
    unchanged.
- `sdd-check`: one table row C20–C24, the rows in the functional (C20, C22) and full (C21, C23, C24) scopes, input
  § 1 g `similar=` (a C21/C24 line on the scope is a `high` finding, a candidate is judged by reading both artifacts, a
  missing `similar=` is `high | duplicate check not run`), routing in § 4 (C20, C22 to `sdd-clarify`; C21, C23, C24
  to `sdd-plan`). New reference `references/duplicates.md` (39 lines): what the tool compares per row, how to judge a
  candidate with a legitimate example each, how to fix a finding, the `C24` baseline for a legacy spec.

Choices:
- C21 and C24 are hard failures in `similar` only, not in `check`: C21 is already a `check_spec.py` failure (rule
  `enabler-contract`), and C24 in `check` would fail every spec with an old collision (33 in the Stratics copy below)
  with no baseline in `spec_trace.py`; `sdd-check` blocks on them, with its own `baseline.json` rows for a legacy spec.
- Exact equality of normalized word sets, no similarity threshold: deterministic, no tuning, and on the Stratics copy a
  title Jaccard of 0.7 or more finds no pair either, so a threshold would add noise without recall there.
- `sdd-clarify` and `sdd-plan` are unchanged: they already run `sdd-check`, which now asks for `similar=`.

## Proof

- Red first: `test_spec_trace_similar.py` (17 tests) failed 17 of 17 before the change (no `similar` command, no
  `similar_words`/`statement_parts`); two more (statement words, one line per pair) were written with the statement
  fallback. 19 green under `python3.12` and `/usr/bin/python3` 3.9.
- Byte for byte: `check_spec.py` (full and `-S`), `spec_trace.py check`, `status`, `lint`, `enablers`, `versions` and
  the rendered matrix on `platforms/ci/fixtures/consumer` and on a copy of Stratics' `docs/spec` (local
  `stratics-docs` checkout, 97 FEATs, 505 REQs), both Pythons, before and after: 32 outputs, no difference.
- `similar` on the Stratics copy: 33 C24 findings (REQs listed by two to eleven open FEATs among its 49 open FEATs; the
  E § 13.1 count of 3 was on a later `origin/main`) and 0 candidates (no process, no `Use case:` line, no REQ statement
  in the template's form, no equal statement or title words); on the fixture consumer: 0 and 0.
- `bash platforms/tools/check.sh`, `bash platforms/tools/check.sh --links`,
  `python3.12 platforms/tools/run_tests.py --layer unit,contract`, `--layer integration --changed-from
  origin/feat/kit-096-versioned-feat`.

## History

- 2026-11-16: confirmed (owner, E § 17, backlog G11).
- 2026-11-17: implemented on `feat/kit-097-duplicate-checks`, cut from `feat/kit-096-versioned-feat` (KIT-096 is not
  on main yet); PR pending.
