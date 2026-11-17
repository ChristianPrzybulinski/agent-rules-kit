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
  - Findings (mechanical), exit 1: C21 a contract id two ENBs provide; C24 a REQ in the Scope of two open blocks, each a
    versioned FEAT's last block while not validated, delivered or cancelled. A FEAT without `## Versions` takes no
    part: blocks are KIT-096's, and FEATs written before the use-case model share REQs by design.
  - Candidates (judgment), exit 0: C20 two REQs with the same actor, trigger and result (a statement in the template's
    form "The system must <result>, when <trigger>, for <actor>."), else the same statement words, else the same
    title words; C22 two processes with the same Trigger words and an Actors line in common; C23 two FEATs with the
    same `- Use case:` words or a process step both declare (`declared_steps`, KIT-096).
  - Retired REQs and processes and cancelled FEATs take no part. `check`, `generate` and every other command are
    unchanged.
- `sdd-check`: one table row C20–C24, the rows in the functional (C20, C22) and full (C21, C23, C24) scopes, input
  § 1 g `similar=` (a C21/C24 line on the scope is a `high` finding, a candidate is judged by reading both artifacts, a
  missing `similar=` is `high | duplicate check not run` only when `docs/spec/processes/` or `docs/spec/enablers/`
  exists or a FEAT has `## Versions`, otherwise a note), routing in § 4 (C20, C22 to `sdd-clarify`; C21, C23, C24
  to `sdd-plan`). New reference `references/duplicates.md` (41 lines): what the tool compares per row, how to judge a
  candidate with a legitimate example each, how to fix a finding.

Choices:
- C21 and C24 are hard failures in `similar` only, not in `check`: C21 is already a `check_spec.py` failure (rule
  `enabler-contract`), and `sdd-check` blocks on both.
- C24 reads versioned FEATs only (coordinator review of 8c97da8): counting every open unversioned FEAT as a block gave
  33 findings on the Stratics copy, REQs shared between FEATs as the pre-use-case model writes them, and would have
  blocked every such FEAT's `sdd-check`.
- A missing `similar=` blocks only where C21–C24 can fire (processes, enablers or a versioned FEAT); elsewhere only
  C20, a judgment aid, is lost, so a spec without them blocks exactly as before.
- Exact equality of normalized word sets, no similarity threshold: deterministic, no tuning, and on the Stratics copy a
  title Jaccard of 0.7 or more finds no pair either, so a threshold would add noise without recall there.
- `sdd-clarify` and `sdd-plan` are unchanged: they already run `sdd-check`, which now asks for `similar=`.

## Proof

- Red first: `test_spec_trace_similar.py` (17 tests) failed 17 of 17 before the change (no `similar` command, no
  `similar_words`/`statement_parts`); two more (statement words, one line per pair) were written with the statement
  fallback. Review fix: the two new tests (two unversioned open FEATs, one versioned and one unversioned, each
  sharing a REQ) failed before the C24 change and pass after; 21 green under `python3.12` and `/usr/bin/python3` 3.9.
- Byte for byte: `check_spec.py` (full and `-S`), `spec_trace.py check`, `status`, `lint`, `enablers`, `versions` and
  the rendered matrix on `platforms/ci/fixtures/consumer` and on a copy of Stratics' `docs/spec` (local
  `stratics-docs` checkout, 97 FEATs, 505 REQs), both Pythons, before and after: 32 outputs, no difference.
- `similar` on the Stratics copy: exit 0, 0 findings (no ENB, no versioned FEAT; before the review fix it counted 33
  C24 lines from unversioned open FEATs) and 0 candidates (no process, no `Use case:` line, no REQ statement
  in the template's form, no equal statement or title words); on the fixture consumer: 0 and 0.
- `bash platforms/tools/check.sh`, `bash platforms/tools/check.sh --links`,
  `python3.12 platforms/tools/run_tests.py --layer unit,contract`, `--layer integration --changed-from
  origin/feat/kit-096-versioned-feat`.

## History

- 2026-11-16: confirmed (owner, E § 17, backlog G11).
- 2026-11-17: implemented on `feat/kit-097-duplicate-checks`, cut from `feat/kit-096-versioned-feat` (KIT-096 is not
  on main yet); PR pending.
