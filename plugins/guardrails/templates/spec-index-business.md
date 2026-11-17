---
project: "[project-name]"
version: "0.1.0"
protocol_version: 1
card_project: null
updated: "YYYY-MM-DD"
# No sdd: block (KIT-087 P4): the process parameters are the sdd section of the project's .ai-kit.yaml, which
# skill sdd-constitution writes; each key, its default and the step that reads it: references/sdd-parameters.md.
---

# [Project name] — Specification

Cover and index. The source of truth for each subject lives in the linked files; here only vision, scope and indexes. Classify claims: `[FACT]` `[DECISION]` `[PROPOSAL]` `[HYPOTHESIS]` `[BLOCKER]`.

Regimes: spec-anchored (maintained and validated for the life of the product) = protocol schemas and examples, content schemas, decisions, requirements, journeys (where the project has them) and this index.
Spec-first (written to frame and cut the work, then frozen as history) = NEED files, FEAT bodies and task tables; task status is derived from each row's item and FEAT status from its rows up to `in-progress`; `validated` and `delivered` are written by `spec_trace.py validate` and `deliver`; none is edited by hand.

<!-- The spec.md template of project.kind business (init-spec.sh copies it; spec-index-game.md is the game one).
     Register (skills/sdd-constitution/references/sdd-process.md, Register): Vision to Out of scope in PO language, the
     experience the product promises; technical choices live in Architecture, decisions and FEATs.
     Optional vision sections: Pillars, Core loop, Direction and References stay only when sdd.vision_sections lists
     them; sdd-constitution deletes the others and adds any other heading the key lists after References. -->

## Vision

[3 lines: what it is, for whom, what makes it different.]

## Pillars
<!-- Optional (sdd.vision_sections). Product principles: three to five promises to the user that every NEED serves.
     A NEED names the pillar it serves (Triage, Pillar: P<n>); sdd-specify parks or rejects one that serves none,
     citing this table, and sdd-check C13 flags it. Ids are never reused. -->

| Id | Pillar | Rules out |
|---|---|---|
| P1 | [a promise to the user, one sentence: "Any task takes at most three steps"] | [the kind of work it refuses] |

## Core loop
<!-- Optional (sdd.vision_sections). The loop a returning user repeats, as actions and visible results. -->

[trigger → action → visible result → reason to come back]

## Direction
<!-- Optional (sdd.vision_sections). Brand, tone and visual style in a few lines, each with the approved mock or style
     guide that holds it. -->

- Tone: [...]
- Visual: [... — approved mock or style guide path]

## References
<!-- Optional (sdd.vision_sections). Products and works this one learns from: what it takes and what it leaves. -->

| Reference | Take | Leave |
|---|---|---|
| [product or work] | [what to follow] | [what not to] |

## First-delivery scope
<!-- Counted: every item carries a number (screens, roles, integrations, regions), so a NEED is checked against it. -->

| Item | Count |
|---|---|
| [screens, roles, integrations or regions] | [n] |

## Out of scope (explicit)
<!-- One line per refused or deferred area, with why and until when. sdd-specify closes a NEED that hits a line
     rejected (never) or parked (later), citing the line; sdd-check C13 flags it. -->

- [area — why; never | after <milestone>]

## Glossary
<!-- sdd-constitution seeds it; sdd-clarify adds each domain term a REQ uses. Domain terms only: the kit defines the
     process terms (NEED, REQ, FEAT, decision, debt). -->

| Term | Definition | Source |
|---|---|---|
| [Term] | [1 sentence] | [doc/legacy/decision] |

## Architecture
<!-- sdd-constitution. The base architecture in one line with the decision that records it, then one row per area: a
     part of the code a change is counted against (sdd-tasks sizes a task row by the areas it touches; sdd-plan places
     the design in them). With docs/spec/enablers/, the table is the ENB index: one row per enabler, the Area cell
     links its file (`enablers/ENB-001-billing.md`), Paths repeats its Code paths and Holds its bounded
     context in one line; sdd-tasks then sizes a row by the ENB it changes, and a part outside every ENB (build,
     tooling) keeps a plain area row. -->

[Base architecture in one line, for example "authoritative server, thin client" — DEC-nnn.]

| Area | Paths | Holds |
|---|---|---|
| [area, or the ENB id linked to its `enablers/ENB-nnn-slug.md`] | [rooted folder or glob] | [what lives there, one line] |

## Governance
<!-- A pointer, never a copy (KIT-099): the profile's approval keys and protected paths, each decision's deciders,
     each ENB's and process's owner, each tech process's trigger and runs, each debt's payment stay in their files. -->

Who decides, approves, owns and runs what: `spec_trace.py governance docs/spec`, generated on demand.

## Reading order for a new session

1. `AGENTS.md`
2. This file
3. `decisions/` with status `approved`
4. The `FEAT` in progress (status `in-progress`, derived)

## Indexes

### Needs

| ID | Title | Type | Status |
|---|---|---|---|

### Features

| ID | Title | Status | Card | Flag |
|---|---|---|---|---|

### Functional requirements

| ID | Title | Features |
|---|---|---|

### Non-functional requirements

| ID | Title | Metric | Features |
|---|---|---|---|

### Decisions

| ID | Title | State | Date |
|---|---|---|---|

### Debts

| ID | Title | Payment trigger | State |
|---|---|---|---|
