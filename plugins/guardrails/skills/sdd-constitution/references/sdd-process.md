---
description: SDD flow, entry points, step outputs, identifiers, statuses, journeys and project specification layout.
kind: detail
---

# SDD — Spec-Driven Development

Adapted from [github/spec-kit](https://github.com/github/spec-kit) as repository skills; project artifacts live under `docs/spec/`, never in the kit.

Entry points: vague idea → `/grilling` first, then `sdd-specify` when problem/value is describable; described feature → `sdd-specify`; new project/principles → `sdd-constitution`; one user-visible flow → `sdd-journey`; vague feel question (movement, camera, battle feedback, UI) → `sdd-spike`, whose report feeds `sdd-specify` and whose branch never merges.

## Flow

Repeat `implement → review` per issue until READY. Run `to-card` after `tasks` to cut one issue per task row (wave order) and after delivery to close; `implement` runs in one worktree per issue and opens one PR per issue, which the architect reviews before merge.

| Step | Skill | Input | Output |
|---|---|---|---|
| 0 | `sdd-constitution` | product/stack | project rules + spec index |
| 1 | `sdd-specify` | feature description | proposed FEAT + REQs |
| 2 | `sdd-clarify` | FEAT questions | clarified FEAT |
| 3 | `sdd-check` | clarified FEAT + artifacts | validator, consistency and quality report |
| 4 | `sdd-plan` | checked FEAT | Plan + DECs; planned |
| 5 | `sdd-tasks` | Plan | ordered task rows |
| 6 | `sdd-implement` | one task issue | code/tests/docs; PR per issue |
| 7 | `review` | FEAT + delivery | READY/PARTIAL/NOT READY |
| 8 | `sdd-to-card` | task rows + FEAT | one issue per task, FEAT card |

## Identifiers and status

`FEAT-nnn` → `features/`; `REQ-F-nnn`/`REQ-NF-nnn` → `requirements/`; `DTEC-nnn`/`DGME-nnn`/`DPRO-nnn` → `decisions/`; `DEBT-nnn` → `debts/`; `J-nn` → `journeys/`. Number sequentially per kind namespace (DTEC, DGME, DPRO); never reuse.

Feature status moves forward: `proposed → clarified → planned → in-progress → validated → delivered` (or `cancelled`). From `in-progress` on the value is derived (see Regimes). During implementation the executor's state is `docs/spec/progress/FEAT-nnn.json` (`passes` per task, set only after the literal proof output); after merge the task row and FEAT status derived from GitHub are the source of truth and the progress file is advisory. `delivered` means merged to `main` with no flag or the flag on. Journeys: `proposed → approved` (or `retired`).

Every spec/decision classifies claims as `[FACT]`, `[DECISION]`, `[PROPOSAL]`, `[HYPOTHESIS]` or `[BLOCKER]`.

## Regimes

Two regimes, after Böckeler/Thoughtworks (2025-10: spec-first, spec-anchored, spec-as-source; the kit has no spec-as-source):
- spec-anchored: maintained and validated for the life of the product: `protocol/` schemas and examples, content schemas, decisions (DTEC/DGME/DPRO), requirements (REQ-F/REQ-NF), journeys (where the project has them) and the `spec.md` index. Every change is a reviewed PR.
- spec-first: FEAT bodies and task tables. Written to cut the work, frozen as history once delivered; FEAT `status` and task `State` are derived by tooling from GitHub, never edited by hand.

## Project layout

```text
docs/spec/
├── spec.md
├── features/FEAT-nnn-slug.md
├── requirements/{functional,non-functional}/REQ-*.md
├── decisions/DTEC-nnn-slug.md
├── debts/DEBT-nnn-slug.md
├── progress/FEAT-nnn.json
└── journeys/J-nn.md
```

Templates: `../../../templates/spec-*.md`. Bootstrap: `platforms/kits/sdd/init-spec.sh <repo>`.

