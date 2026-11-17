---
id: KIT-098
title: "Our pattern: SysML link names, DDD, Backstage for ENBs and SAFe in one reference, with generated views"
status: in-progress
confirmed: "2026-11-16 (owner, kit chat: \"Sim, faça\" on E § 17, backlog G12)"
issue: "#340"
pr: ""
---

# KIT-098 — Our pattern: SysML link names, DDD, Backstage for ENBs and SAFe in one reference, with generated views

## Problem and evidence

[FACT] The owner's game-profile evaluation (`KIT-GAME-PROFILE-EVALUATION-2026-11-16.md` in the owner's workspace,
"E" below) § 13.4 picks one pattern for the spec artifacts: SysML gives the link vocabulary (derive, satisfy, verify,
refine, allocate), DDD the enabler's content, Backstage the enabler's field names and an export, SAFe the work
hierarchy. § 15 amends it: a process holds N FEATs and a FEAT is a SysML use case, which Backstage has no kind for, so
the export covers ENBs only. KIT-095 shipped the ENB with Backstage's field names, but no reference states the pattern,
the matrix names no link, and no tool writes `catalog-info.yaml`.

## Change

- `plugins/guardrails/skills/sdd-constitution/references/pattern.md` (new, `kind: detail`): the E § 13.4 table with
  the § 15 FEAT row, the five links with where each is written once and where it is generated, and the two outputs.
  `sdd-constitution/SKILL.md` names it in its pointer line.
- `platforms/ci/validations/spec_trace.py` (new functions, one-line call sites):
  - `link_views`: the matrix's new last section, Links (SysML): per REQ its `derive` steps (journey or process step
    Rules), `refine` FEATs (FEAT `requirements`), `satisfy` ENBs (Aggregates, Qualities) and `verify` tests; per FEAT
    its REQs and `allocate` ENBs (FEAT `enablers`).
  - `catalog SPEC --out FILE [--force]`: Backstage entities (`backstage.io/v1alpha1`) as multi-document YAML from
    `yaml.safe_dump_all`: a Component per ENB (`type: service`, lifecycle from status, owner, system, providesApis,
    consumesApis, dependsOn with the `component:` ENBs and the `resource:` contracts it requires; `domain` as the
    annotation `agent-rules-kit/domain`, since a Component has no domain field), an API per api (`openapi`), message or
    event (`asyncapi`) contract and a Resource per other contract with `dependencyOf` its ENB. Refused: an existing
    file without `--force`, a path inside the kit checkout, any load error or an empty owner. Off without `enablers/`.
  - `diagram SPEC PROC-nnn`: a Mermaid `flowchart TD` of the main steps in order and each alternative from its `At`.

Choice on existing output: the link names go into a new view, rendered only when the spec has `processes/` or
`enablers/`. The existing views keep their headings, so a spec with neither renders byte for byte as before, and since
both folders arrive in the same unreleased version (KIT-090, KIT-095), no released project's `traceability.md`
changes. Not breaking; no Migration line.

## Proof

New `platforms/ci/validations/test_spec_trace_pattern.py` (16 tests, red before the code: 3 failures and 12 errors),
then green with `python3.12` and `/usr/bin/python3` 3.9; the catalog tests parse the output back with PyYAML.
Byte-for-byte: `render_matrix` sha-256 and `spec_trace.py check` output are the same under `origin/main` and this
branch, on Python 3.12 and 3.9, for `platforms/ci/fixtures/consumer/docs/spec` and a copy of Stratics' `docs/spec`.
Gates: `bash platforms/tools/check.sh`, `check.sh --links`, `python3.12 platforms/tools/run_tests.py --layer
unit,contract` and `--layer integration --changed-from origin/main`.

## History

- 2026-11-16: confirmed (owner, #340 from E § 17).
- 2026-11-17: implemented on `feat/kit-098-pattern-reference`.
