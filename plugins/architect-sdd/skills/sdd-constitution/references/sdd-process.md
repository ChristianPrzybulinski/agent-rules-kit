---
description: SDD flow, entry points, step outputs, identifiers, statuses, journeys and project specification layout.
kind: detail
---

# SDD — Spec-Driven Development

Adapted from [github/spec-kit](https://github.com/github/spec-kit) as repository skills; project artifacts live under `docs/spec/`, never in the kit.

Entry points: vague idea → `/grilling` first, then `sdd-specify` when problem/value is describable; described feature → `sdd-specify`; new project/principles → `sdd-constitution`; one user-visible flow → `sdd-journey`.

## Flow

Repeat `implement → validate` per issue until READY. Run `to-card` after `tasks` to cut one issue per task row (wave order) and after delivery to close; `implement` runs in one worktree per issue and opens one PR per issue, which the architect reviews before merge.

| Step | Skill | Input | Output |
|---|---|---|---|
| 0 | `sdd-constitution` | product/stack | project rules + spec index |
| 1 | `sdd-specify` | feature description | proposed FEAT + REQs |
| 2 | `sdd-clarify` | FEAT questions | clarified FEAT |
| 3 | `sdd-analyze` | related artifacts | consistency report |
| 4 | `sdd-audit` | clarified FEAT | quality checklist/gaps |
| 5 | `sdd-plan` | audited FEAT | Plan + DECs; planned |
| 6 | `sdd-tasks` | Plan | ordered task rows |
| 7 | `sdd-implement` | one task issue | code/tests/docs; PR per issue |
| 8 | `validate-implementation` | FEAT + delivery | READY/PARTIAL/NOT READY |
| 9 | `sdd-to-card` | task rows + FEAT | one issue per task, FEAT card |

## Identifiers and status

`FEAT-nnn` → `features/`; `REQ-F-nnn`/`REQ-NF-nnn` → `requirements/`; `DTEC-nnn`/`DGME-nnn`/`DPRO-nnn` → `decisions/`; `DEBT-nnn` → `debts/`; `J-nn` → `journeys/`. Number sequentially per kind namespace (DTEC, DGME, DPRO); never reuse.

Feature status moves forward: `proposed → clarified → planned → in-progress → validated → delivered` (or `cancelled`). `delivered` means merged to `main` with no flag or the flag on. Journeys: `proposed → approved` (or `retired`).

Every spec/decision classifies claims as `[FACT]`, `[DECISION]`, `[PROPOSAL]`, `[HYPOTHESIS]` or `[BLOCKER]`.

## Project layout

```text
docs/spec/
├── spec.md
├── features/FEAT-nnn-slug.md
├── requirements/{functional,non-functional}/REQ-*.md
├── decisions/DTEC-nnn-slug.md
├── debts/DEBT-nnn-slug.md
└── journeys/J-nn.md
```

Templates: `../../../templates/spec-*.md`. Bootstrap: `platforms/kits/sdd/init-spec.sh <repo>`.

