---
description: SDD flow, entry points, step outputs, identifiers, statuses, journeys and project specification layout.
kind: detail
---

# SDD — Spec-Driven Development

Adapted from [github/spec-kit](https://github.com/github/spec-kit) as repository skills; project artifacts live under `docs/spec/`, never in the kit.

Entry: every request (idea, need, improvement, problem) is recorded by `sdd-intake` as a `NEED-nnn`. `sdd-specify` decides its type, route and priority: `new`, `improvement`, `platform` and `decision` go on to refinement, a `fix` of behavior an artifact already states and a `content`-only change are routed without it. The NEED (business) becomes REQs (functional, `sdd-clarify`), then a FEAT (technical, `sdd-plan`). A vague idea is stress-tested with `/grilling`, a feel question (motion, camera, feedback, UI) gets an `sdd-spike`, whose report becomes the NEED's evidence and whose branch never merges. A new project or new principles start with `sdd-constitution`.

## Flow

Repeat `implement → review` per issue until READY. Run `to-card` after `tasks` to cut one issue per task row (wave order) and after delivery to close; `implement` runs in one worktree per issue and opens one PR per issue, which the architect reviews before merge.

| Step | Skill | Input | Output |
|---|---|---|---|
| 0 | `sdd-constitution` | product/stack | project rules + spec index |
| entry | `sdd-intake` | request | NEED proposed |
| 1 | `sdd-specify` | proposed NEED; later the triaged one | decide: triaged, or closed; describe: specified |
| 2 | `sdd-clarify` | specified NEED | REQs (new, amended), journeys, product decisions; NEED refined |
| 3 | `sdd-check` | NEED (functional) or FEAT (technical) | read-only report that blocks refined or tasks |
| 4 | `sdd-plan` | refined NEED | FEAT with technical criteria, Plan + decisions; planned |
| 5 | `sdd-tasks` | Plan | ordered task rows |
| 6 | `sdd-implement` | one task issue | code/tests/docs; PR per issue |
| 7 | `review` | FEAT + delivery | READY/PARTIAL/NOT READY |
| 8 | `sdd-to-card` | task rows + FEAT | one issue per task, FEAT card |

## Identifiers and status

`NEED-nnn` → `needs/`; `FEAT-nnn` → `features/`; `REQ-F-nnn`/`REQ-NF-nnn` → `requirements/`; `DEC-nnn` → `decisions/`; `DEBT-nnn` → `debts/`; `J-nn` → `journeys/`. A project that numbers decisions per kind declares `decision_kinds` (kind → prefix) in `spec.md`; each decision then carries its `kind` and that kind's prefix. Number sequentially inside each prefix; never reuse. When two or more spec sessions run against one specification at the same time, each session's prompt reserves a block of ids for every kind it may create (`NEED`, `FEAT`, `REQ-F`, `REQ-NF`, `DEC` or each declared decision prefix, `DEBT`, `J`); a session takes ids only from its own block. A reserved id left unused stays a gap and is never reused.

A NEED moves `proposed → triaged → specified → refined → delivered`, or closes `rejected`, `merged`, `routed` or `parked` (a parked NEED returns to `triaged` when taken up): `triaged` once product confirms type, route and priority (the agent routes a fix or a duplicate, which product reviews later), `specified` once its outcome, Situations, scope and constraints are written, `refined` once product approves its REQs after a clean functional check, `delivered` once every FEAT it lists is delivered. Its links are written only in the NEED. A REQ moves `proposed → approved` (or `retired`; absent means `approved`) and is listed by the FEATs that implement it, or by its NEED until `sdd-plan` creates one. Journeys (`proposed → approved` or `retired`) are written inside `sdd-clarify` and checked by `sdd-check`, only where the project keeps them. A FEAT moves `proposed → planned → in-progress → validated → delivered` (or `cancelled`; `clarified` remains on FEATs older than the NEED flow); from `in-progress` on the value is derived (see Regimes). During implementation the executor's state is `docs/spec/progress/FEAT-nnn.json` (`passes` per task, set only after the literal proof output); after merge the task row and FEAT status derived from GitHub are the source of truth and the progress file is advisory. `delivered` means merged to `main` with no flag or the flag on.

Every spec/decision classifies claims as `[FACT]`, `[DECISION]`, `[PROPOSAL]`, `[HYPOTHESIS]` or `[BLOCKER]`.

## Regimes

Two regimes, after Böckeler/Thoughtworks (2025-10: spec-first, spec-anchored, spec-as-source; the kit has no spec-as-source):
- spec-anchored: maintained and validated for the life of the product: `protocol/` schemas and examples, content schemas, decisions, requirements (REQ-F/REQ-NF), journeys (where the project has them) and the `spec.md` index. Every change is a reviewed PR.
- spec-first: NEED files, FEAT bodies and task tables. Written to frame and cut the work, frozen as history once delivered or closed; FEAT `status` and task `State` are derived by tooling from GitHub, never edited by hand.

## Project layout

```text
docs/spec/
├── spec.md
├── needs/NEED-nnn-slug.md (+ NEED-nnn-data/ when the evidence is bulky)
├── features/FEAT-nnn-slug.md
├── requirements/{functional,non-functional}/REQ-*.md
├── decisions/DEC-nnn-slug.md
├── debts/DEBT-nnn-slug.md
├── progress/FEAT-nnn.json
└── journeys/J-nn.md
```

Templates: `../../../templates/spec-*.md`. Bootstrap: `platforms/kits/sdd/init-spec.sh <repo>`.

