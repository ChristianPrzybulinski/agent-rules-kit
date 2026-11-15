---
description: SDD flow, entry points, step outputs, identifiers, statuses, journeys and project specification layout.
kind: detail
---

# SDD — Spec-Driven Development

Adapted from [github/spec-kit](https://github.com/github/spec-kit) as repository skills; project artifacts live under `docs/spec/`, never in the kit.

Entry: every request (idea, need, improvement, problem) is recorded by `sdd-intake` as a `NEED-nnn`. `sdd-specify` decides its type, route and priority: `new`, `improvement`, `platform` and `decision` go on to refinement, a `fix` of behavior an artifact already states and a `content`-only change are routed without it. The NEED (business) becomes REQs (functional, `sdd-clarify`), then a FEAT (technical, `sdd-plan`). A vague idea is stress-tested with `/grilling`; a bug with no named cause goes through `investigate` and a feel or feasibility question through an `sdd-spike` (its branch never merges), and both reports enter `sdd-intake` as the NEED's evidence. A new project or new principles start with `sdd-constitution`. A project turns parts of this flow on or off and sets its limits in the `sdd:` block of `docs/spec/spec.md` (`sdd-parameters.md`); it never copies a step to change it.

The chain is intake → specify → clarify → plan → tasks (the cut included) → implement → review → sdd-review → sdd-release. `sdd-check` is not a step: it is the read-only tool that `sdd-clarify` calls in its functional scope (blocks `refined`) and `sdd-plan` in its full scope (the functional items again plus the technical ones, blocks `planned`); anyone may run it as an audit (`all`).

## Flow

`sdd-plan` makes one FEAT per delivery and splits a NEED whose work would exceed `max_feat_tasks` rows. `sdd-tasks` writes the FEAT's task rows in a spec PR, then, once that table is approved or merged, cuts one item per row or bundle in wave order: a GitHub issue, or a `TASK-nnn` file with `tracker: none`; its resync keeps rows and items aligned after a change. Repeat `implement → review` per PR until READY: `implement` takes one item, a FEAT's ready items wave by wave, or a PR's findings (fix mode), in one worktree per PR (`pr_unit`); `review` runs in another context, and no one merges a PR they wrote. After each wave the broad suite runs once on `main`; a red `main` stops merges and gets a fix row. When a FEAT's last row merges, `sdd-review` closes it on `main`; `sdd-release` takes validated FEATs to the product, and its feedback re-enters `sdd-intake` as child NEEDs.

| Step | Skill | Input | Output |
|---|---|---|---|
| 0 | `sdd-constitution` | product/stack | project rules + spec index |
| entry | `sdd-intake` | request | NEED proposed |
| 1 | `sdd-specify` | proposed NEED; later the triaged one | decide: triaged, or closed; describe: specified |
| 2 | `sdd-clarify` | specified NEED | REQs (new, amended), journeys, product decisions; NEED refined |
| tool (was 3) | `sdd-check` | called by clarify (NEED, functional) and plan (FEAT, full); `all` for audits | read-only report that blocks refined or planned |
| 4 | `sdd-plan` | refined NEED | FEAT with technical criteria, Plan + decisions; planned |
| 5 | `sdd-tasks` | planned FEAT | task rows (spec PR), then one cut item per row or bundle |
| 6 | `sdd-implement` | a cut item, a FEAT's ready items or a PR's findings | code/tests/docs; PR per `pr_unit` with Red, Proof and executor line |
| 7 | `review` | one delivery (PR) | READY/PARTIAL/NOT READY; findings with owner and `close_when` |
| 8 | `sdd-review` | FEAT whose last row merged | closure on `main`; FEAT validated (delivered under `release: merge`) |
| 9 | `sdd-release` | validated FEATs | release, acceptance, flag on; FEAT and NEED delivered |

## Identifiers and status

`NEED-nnn` → `needs/`; `FEAT-nnn` → `features/`; `REQ-F-nnn`/`REQ-NF-nnn` → `requirements/`; `DEC-nnn` → `decisions/`; `DEBT-nnn` → `debts/`; `TASK-nnn` → `tasks/` (`tracker: none`); `J-nn` → `journeys/`. A project that numbers decisions per kind declares `decision_kinds` (kind → prefix) in `spec.md`; each decision then carries its `kind` and that kind's prefix. Number sequentially inside each prefix; never reuse. When two or more spec sessions run against one specification at the same time, each session's prompt reserves a block of ids for every kind it may create (`NEED`, `FEAT`, `REQ-F`, `REQ-NF`, `DEC` or each declared decision prefix, `DEBT`, `TASK`, `J`); a session takes ids only from its own block. A reserved id left unused stays a gap and is never reused.

A NEED moves `proposed → triaged → specified → refined → delivered`, or closes `rejected`, `merged`, `routed` or `parked` (a parked NEED returns to `triaged` when taken up): `triaged` once product confirms type, route and priority (the agent routes a fix or a duplicate, which product reviews later), `specified` once its outcome, Situations, scope and constraints are written, `refined` once product approves its REQs after a clean functional check, `delivered` once every FEAT it lists is delivered (set with its last FEAT by `spec_trace.py deliver`, or `validate` under `release: merge`; a `decision` NEED with no FEAT, by the approval of its decision record in `sdd-clarify`). Its links are written only in the NEED. A REQ moves `proposed → approved` (or `retired`; absent means `approved`) and is listed by the FEATs that implement it, or by its NEED until `sdd-plan` creates one. Journeys (`proposed → approved` or `retired`) are written inside `sdd-clarify` and checked by `sdd-check`, only where the project keeps them. A FEAT moves `proposed → planned → in-progress → validated → delivered` (or `cancelled`; `clarified` remains on FEATs older than the NEED flow); task rows derive `in-progress` at most; `validated` (the closure passed on `main`) is written only by `sdd-review` and `delivered` (released and accepted, flag on or none) only by `sdd-release`, or by `sdd-review` under `release: merge`, each through `spec_trace.py validate`/`deliver` with the History line `check_spec.py` requires. A task row's `Status` (`todo`, `doing`, `blocked`, `done`, `cancelled`) is derived from its item: the GitHub issue, or the `TASK-nnn` file's `status`; a FEAT cut before KIT-068 may keep `docs/spec/progress/FEAT-nnn.json`, which `check_spec.py` still validates and `sdd-implement` never orients on. Every spec/decision classifies claims as `[FACT]`, `[DECISION]`, `[PROPOSAL]`, `[HYPOTHESIS]` or `[BLOCKER]`. `baseline.json` holds old `check_spec.py` and `sdd-check all` findings per rule so they neither block nor hide new ones; it only shrinks.

## Regimes

Two regimes, after Böckeler/Thoughtworks (2025-10: spec-first, spec-anchored, spec-as-source; the kit has no spec-as-source):
- spec-anchored: maintained and validated for the life of the product: `protocol/` schemas and examples, content schemas, decisions, requirements (REQ-F/REQ-NF), journeys (where the project has them) and the `spec.md` index. Every change is a reviewed PR.
- spec-first: NEED files, FEAT bodies, task tables and `TASK-nnn` files. Written to frame and cut the work, frozen as history once delivered or closed; FEAT `status` and task `Status` are derived by tooling from the items, never edited by hand.

## Project layout

```text
docs/spec/
├── spec.md (+ baseline.json: old findings, only shrinks)
├── needs/NEED-nnn-slug.md (+ NEED-nnn-data/ when the evidence is bulky)
├── features/FEAT-nnn-slug.md
├── requirements/{functional,non-functional}/REQ-*.md
├── decisions/DEC-nnn-slug.md
├── debts/DEBT-nnn-slug.md
├── tasks/TASK-nnn-slug.md (tracker: none)
├── progress/FEAT-nnn.json (FEATs cut before KIT-068)
└── journeys/J-nn.md
```

Templates: `../../../templates/spec-*.md`. Bootstrap: `platforms/kits/sdd/init-spec.sh <repo>`.

