# SDD — Spec-Driven Development

Process adapted from [github/spec-kit](https://github.com/github/spec-kit) (`speckit-*` skills), without the `specify` CLI (requires Python 3.11+/uv). Here the steps are kit skills, and the artifacts live **in the project's repository**, under `docs/spec/` — never in the kit.

## Flow

```text
constitution (1x per project)  →  repo AGENTS.md + docs/spec/spec.md
        │
   specify  →  clarify  →  analyze  →  audit  →  plan  →  tasks  →  implement  →  validate  →  to-card
   FEAT-xxx    questions  spec↔req   gap       technical ordered   code         verdict     GH issue
   REQ-*       resolved   coherence checklist plan      list      + tests      READY?      + status
```

Repeat `implement → validate` until READY. `to-card` can run right after `specify` (opens the card) and again after `validate` (closes it).

| Step | Skill | Input | Output | spec-kit origin |
|---|---|---|---|---|
| 0 | `sdd-constitution` | product request, stack | `AGENTS.md`, `docs/spec/spec.md` | `constitution` |
| 1 | `sdd-specify` | feature description | `features/FEAT-xxx.md` (status `proposta`), `requirements/**/REQ-*.md` | `specify` |
| 2 | `sdd-clarify` | FEAT | questions → answers incorporated; status `clarificada` | `clarify` |
| 3 | `sdd-analyze` | FEAT + REQs + DECs | report of contradictions/gaps/orphans | `analyze` |
| 4 | `sdd-audit` | FEAT | spec quality checklist (testable? complete? safe?) | `checklist` |
| 5 | `sdd-plan` | clarified FEAT | *Plan* section in the FEAT (modules, contract, migration, flag, tests); `DEC-xxx` if a decision; status `planejada` | `plan` |
| 6 | `sdd-tasks` | plan | ordered *Tasks* section, each with a verifiable criterion | `tasks` |
| 7 | `sdd-implement` | tasks | code + tests + docs, one task at a time; status `em-implementação` | `implement` |
| 8 | `core/validate-implementation` | FEAT | verdict READY/PARTIAL/NOT READY; status `validada` | `converge` |
| 9 | `sdd-to-card` | FEAT | GitHub issue (Projects) synced with status | — (addition) |

## Identifiers

| Prefix | Where | Example |
|---|---|---|
| `FEAT-nnn` | `docs/spec/features/` | `FEAT-003-login.md` |
| `REQ-F-nnn` | `docs/spec/requirements/functional/` | `REQ-F-012-argon2-password.md` |
| `REQ-NF-nnn` | `docs/spec/requirements/non-functional/` | `REQ-NF-004-battle-latency.md` |
| `DEC-nnn` | `docs/spec/decisions/` | `DEC-002-websocket-vs-tcp.md` |
| `DEBT-nnn` | `docs/spec/debts/` | `DEBT-001-old-login-flag.md` |

Sequential numbering per type, never reused. File name: `PREFIX-nnn-slug.md`. Frontmatter validated by `platforms/ci/schemas/*.schema.json` (CI via `platforms/kits/github/workflows/spec-lint.yml`).

## Feature status

`proposta → clarificada → planejada → em-implementação → validada → entregue` (+ `cancelada`). Forward only; regression requires a note in *History*. `entregue` = merged to `main` with the flag on (or no flag).

## Mandatory claim classification (in every spec/decision)

`[FACT]` verified with source · `[DECISION]` approved by the product · `[PROPOSAL]` technical, awaiting approval · `[HYPOTHESIS]` to validate, with how to validate · `[BLOCKER]` external dependency.

## Layout in the project

```text
docs/spec/
├── spec.md                      # cover: vision, scope, glossary, FEAT/REQ/DEC/DEBT index
├── features/FEAT-nnn-slug.md
├── requirements/
│   ├── functional/REQ-F-nnn-slug.md
│   └── non-functional/REQ-NF-nnn-slug.md
├── decisions/DEC-nnn-slug.md
└── debts/DEBT-nnn-slug.md
```

Templates in `agents/templates/`. Bootstrap: `platforms/kits/sdd/init-spec.sh <repo>` copies the empty structure.
