# SDD — Spec-Driven Development

Adapted from [github/spec-kit](https://github.com/github/spec-kit) as repository skills; project artifacts live under `docs/spec/`, never in the kit.

## Entry points

- Vague idea → `/grilling` first, then `sdd-specify` when problem/value is describable.
- Described feature → `sdd-specify`; new project/principles → `sdd-constitution`.

## Flow

```text
constitution (once/project) → AGENTS.md + docs/spec/spec.md
        │
   specify → clarify → analyze → audit → plan → tasks → implement → validate → to-card
   FEAT/REQ  answers   gaps      quality  design  order   code/tests  verdict    issue
```

Repeat `implement → validate` until READY. Run `to-card` after specify to open and after delivery to close.

| Step | Skill | Input | Output |
|---|---|---|---|
| 0 | `sdd-constitution` | product/stack | project rules + spec index |
| 1 | `sdd-specify` | feature description | proposed FEAT + REQs |
| 2 | `sdd-clarify` | FEAT questions | clarified FEAT |
| 3 | `sdd-analyze` | related artifacts | consistency report |
| 4 | `sdd-audit` | clarified FEAT | quality checklist/gaps |
| 5 | `sdd-plan` | audited FEAT | Plan + DECs; planned |
| 6 | `sdd-tasks` | Plan | ordered task rows |
| 7 | `sdd-implement` | Tasks | code/tests/docs; in-progress |
| 8 | `validate-implementation` | FEAT + delivery | READY/PARTIAL/NOT READY |
| 9 | `sdd-to-card` | FEAT | synchronized GitHub issue |

## Identifiers and status

`FEAT-nnn` → `features/`; `REQ-F-nnn`/`REQ-NF-nnn` → `requirements/`; `DEC-nnn` → `decisions/`; `DEBT-nnn` → `debts/`. Number sequentially per type; never reuse.

Feature status moves forward: `proposed → clarified → planned → in-progress → validated → delivered` (or `cancelled`). `delivered` means merged to `main` with no flag or the flag on.

Every spec/decision classifies claims as `[FACT]`, `[DECISION]`, `[PROPOSAL]`, `[HYPOTHESIS]` or `[BLOCKER]`.

## Project layout

```text
docs/spec/
├── spec.md
├── features/FEAT-nnn-slug.md
├── requirements/{functional,non-functional}/REQ-*.md
├── decisions/DEC-nnn-slug.md
└── debts/DEBT-nnn-slug.md
```

Templates: `../../../templates/spec-*.md`. Bootstrap: `platforms/kits/sdd/init-spec.sh <repo>`.
