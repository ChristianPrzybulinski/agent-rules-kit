---
id: KIT-095
title: "The enabler artifact ENB-nnn per bounded context, its contract catalog and the C18 and C19 tool"
status: done
confirmed: "2026-11-16 (owner, kit chat: \"Sim, faça\" on E § 17, backlog G10)"
issue: "#337"
pr: "#355"
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

Part 1 (PR #355), the artifact and its tools:

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

Part 2 (branch `feat/kit-095-part2-enabler-skills`), the skills that plan, check, cut and close with enablers. Each
change applies only with `docs/spec/enablers/`:

- `sdd-plan` § 3 sets the FEAT's `enablers` (and `kind: enabler`); § 4 makes Plan § Contract cite catalog rows as
  `ENB-nnn:<contract>`, a new contract getting its Provided contracts row in the spec PR. Design ends with the walk
  table `| Step | REQ | ENB contract | Task |`: process step → REQ → ENB contract → task. A REQ no ENB satisfies
  gets its Aggregates or Qualities row in that PR. `spec-feature.md` carries the two notes as comments.
- `sdd-check`: rows C18 and C19 (ids free: the table held C1–C15 and C26) in the full scope, and § 1 f. The calling
  session pastes `spec_trace.py enablers --feat FEAT-nnn` after `enablers=` and `spec_trace.py check` after
  `trace=`; both are required, because `enablers` prints OK while `check` fails an ENB table error (#356 item 2). Protocol
  schemas pass the catalog check through `sdd.row_checks.protocol.schemas`; a migration needs `--catalog <glob>`.
- `sdd-tasks` § 2 sizes a row by ENB (one ENB's code and its contracts; work across two ENBs splits at the contract,
  provider first); § 3 writes the row ids into the walk table's Task cells.
- `sdd-review` § 5 and `closure-record.md`: an Enablers closure row (`enablers --feat` and `check`), then `generate`
  after `validate`, so `traceability.md` § Enablers, each ENB's generated History, lists the FEAT with its new
  status in the closure commit.
- `spec-index-business.md` and `spec-index-game.md`: the Architecture comment says the table is the ENB index when
  `enablers/` exists, and `sdd-constitution` § 3 drops its "only while sdd-tasks sizes rows by the area paths".

Moved out: the profile key for the migration folder belongs to KIT-087 P2b, which owns the profile. Until it lands,
the skills pass the folder with `--catalog`.

## Proof

`platforms/tools/check.sh`, `check.sh --links`, `python3.12 platforms/tools/run_tests.py --layer unit,contract` and
`--layer integration --changed-from origin/main`; new `test_check_spec_enabler.py` and `test_spec_trace_enabler.py`,
red before the code. Backward compatibility: on Stratics' `docs/spec` and on `platforms/ci/fixtures/consumer`,
`check_spec.py` (Python 3.12 and `/usr/bin/python3` 3.9) and `spec_trace.py check` print the same output under
`origin/main` and this branch, the rendered matrix has the same sha-256, and `spec_trace.py enablers` reports off.

Part 2 is text only: `check.sh`, `check.sh --links` and the unit, contract and changed integration layers pass;
`test_init_spec.py` copies the two changed spec-index templates byte for byte.

## History

- 2026-11-16: confirmed (owner, #337 from E § 17).
- 2026-11-17: part 1 implemented on `feat/kit-095-enabler-artifact`; PR #355 merged.
- 2026-11-17: part 2 implemented on `feat/kit-095-part2-enabler-skills`; PR pending; done. The migration-folder
  profile key moved to KIT-087 P2b.
