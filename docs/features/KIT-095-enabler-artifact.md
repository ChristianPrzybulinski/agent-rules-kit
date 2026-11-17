---
id: KIT-095
title: "The enabler artifact ENB-nnn per bounded context, its contract catalog and the C18 and C19 tool"
status: in-progress
confirmed: "2026-11-16 (owner, kit chat: \"Sim, faça\" on E § 17, backlog G10)"
issue: "#337"
pr: ""
---

# KIT-095 — The enabler artifact ENB-nnn per bounded context, its contract catalog and the C18 and C19 tool

## Problem and evidence

[FACT] The owner's game-profile evaluation (`KIT-GAME-PROFILE-EVALUATION-2026-11-16.md` in the owner's workspace,
"E" below) § 12.1: the kit has no enabler artifact. The technical facts of a capability live in a FEAT's Plan, which
freezes on delivery, in decision records and in a one-line Architecture row. In Stratics, 46 of 86 DTEC titles name a
contract, and learning what the battle context offers today takes several decisions plus the protocol schemas. § 12.2
picks a living `ENB-nnn` per bounded context or technical capability, with the FEAT as the frozen delivery that links
REQs and ENBs. § 13.4 and § 17.6 set the pattern: SysML link names, DDD content, Backstage field names, SAFe work
hierarchy (FEAT `kind: feature | enabler`); a FEAT is a versioned use case.

## Change

Part 1 (this PR), the artifact and its tools:

- `plugins/guardrails/templates/spec-enabler.md` (new): frontmatter `id`, `title`, `status`, `owner`, `system`,
  `domain`, `providesApis`, `consumesApis`, `dependsOn` (Backstage's names); sections Context (bounded context,
  ubiquitous language, patterns), Aggregates (invariant, `Rules`: REQ-F ids), Events (publishes or consumes, contract),
  Provided contracts (`Contract`, `Kind`: api, message, event, job, file, table, content, config; `Accessed at`,
  `Schema or file`, `Version`, `Consumers`), Required contracts (`From`: the providing ENB), Qualities (`Rules`: REQ-NF
  ids), Code, and the generated Decisions and History.
- `platforms/ci/schemas/enabler.schema.json` (new); `feature.schema.json` gains `kind` (`feature` or `enabler`) and
  `enablers`; `decision.schema.json` and `debt.schema.json` gain `enablers`.
- `check_spec.py`: validates `enablers/` (schema, or the structural fallback), FEAT, decision and debt `enablers` and
  ENB `dependsOn` links (rule `enabler-link`), one provider per contract id and a provider for each consumed id
  (`enabler-contract`), a `kind: enabler` FEAT with an ENB and no REQ-F (`enabler-kind`); `ENB` is a reserved decision
  prefix.
- `spec_trace.py` (new functions, three call sites): ENB tables against the frontmatter (`providesApis` and
  `consumesApis` hold exactly the table ids), contract kinds, a Required row's `From`, REQ cells and event contracts;
  the matrix adds the Enablers view (contracts, satisfied REQs, and the FEATs, decisions and debts naming each ENB: the
  generated History and Decisions) and the Contracts view, and is required once `enablers/` exists; the new
  `enablers [--feat FEAT-nnn] [--catalog GLOB]` command reports C18 (a REQ of an open FEAT, or a process step, that no
  ENB satisfies) and C19 (a Plan § Contract `ENB-nnn:<contract>` reference the catalog lacks or to an ENB the FEAT does
  not list; a provided contract with no consumer and no `public` mark; a protocol schema or `--catalog` file, such as a
  migration, that no `Schema or file` cell covers).
- Skills: `sdd-constitution` creates `enablers/` and turns the Architecture table into the ENB index, and
  `sdd-process.md` lists ENB ids, regime, register and layout; `sdd-implement` (`living-docs.md`) updates the catalog
  row in the contract PR; `review` step 6 and `delivery-steps.md` make a contract change without an ENB edit a finding.
- `init-spec.sh` is unchanged: enablers are opt-in by the folder, like journeys and processes, so it creates none.

Part 2 (open, after the parallel PRs that own those skills): `sdd-plan` walk table (process step → REQ → ENB contract
→ task) and Plan § Contract citing catalog rows; `sdd-check` rows C18 and C19 calling `spec_trace.py enablers`, and a
schema or migration change passing the catalog check; `sdd-tasks` sizing rows by ENB; `sdd-review` closure; a profile
key for the migration folder in place of `--catalog`.

## Proof

`platforms/tools/check.sh`, `check.sh --links`, `python3.12 platforms/tools/run_tests.py --layer unit,contract` and
`--layer integration --changed-from origin/main`; new `test_check_spec_enabler.py` and `test_spec_trace_enabler.py`,
red before the code. Backward compatibility: on Stratics' `docs/spec` and on `platforms/ci/fixtures/consumer`,
`check_spec.py` (Python 3.12 and `/usr/bin/python3` 3.9) and `spec_trace.py check` print the same output under
`origin/main` and this branch, the rendered matrix has the same sha-256, and `spec_trace.py enablers` reports off.

## History

- 2026-11-16: confirmed (owner, #337 from E § 17).
- 2026-11-17: part 1 implemented on `feat/kit-095-enabler-artifact`.
