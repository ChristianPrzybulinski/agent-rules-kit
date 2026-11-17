---
project: "[project-name]"
version: "0.1.0"
protocol_version: 1
card_project: null
updated: "YYYY-MM-DD"
# Process parameters, written by sdd-constitution with the kit defaults below and plan_sections at the game preset
# (Assets on); each key, its default and the step that reads it: skill sdd-constitution, references/sdd-parameters.md.
# check_spec.py --params prints the resolved block.
sdd:
  needs: true
  # journeys: absent = on when docs/spec/journeys/ exists
  tracker: github
  plan_sections: [Design, Contract, Data, UI, Assets, Flag, Tests, Observability, Risks, Dependencies]
  pr_unit: task
  task_minutes: 30
  row_check: null
  cut_command: null
  max_chain: 4
  max_feat_tasks: 30
  release: merge
  review_rounds: 3
  commits_by: executor
  protected_paths: {}
  bundle: {rows: 1, points: 3, high_rows: 1}
  rule_paths: {}
  components: {}
  spec_index: false
  github: {repo: null, pr_repos: [], aliases: [], blocked_labels: [blocked], progress_labels: ["status:in-progress"]}
  row_checks: {gates: null, tests: [], assets: null, protocol: null, artifacts: null, visual: null, evidence_only: false}
  visual_approval: none
  owner_approvals: [decision]
  doc_structure:
    enabled: false
    exempt: .github/doc-structure-exempt.txt
    headings: ["## What goes here", "## What does not go here"]
    done_index: true
---

# [Project name] — Specification

Cover and index. The source of truth for each subject lives in the linked files; here only vision, scope and indexes. Classify claims: `[FACT]` `[DECISION]` `[PROPOSAL]` `[HYPOTHESIS]` `[BLOCKER]`.

Regimes: spec-anchored (maintained and validated for the life of the product) = protocol schemas and examples, content schemas, decisions, requirements, journeys (where the project has them) and this index.
Spec-first (written to frame and cut the work, then frozen as history) = NEED files, FEAT bodies and task tables; task status is derived from each row's item and FEAT status from its rows up to `in-progress`; `validated` and `delivered` are written by `spec_trace.py validate` and `deliver`; none is edited by hand.

<!-- The spec.md template of project.kind game (init-spec.sh copies it; spec-index-business.md is the other one).
     Register (skills/sdd-constitution/references/sdd-process.md, Register): Vision to Out of scope in the player's
     and the designer's language, the experience the game promises; engine, code and data choices live in
     Architecture, decisions and FEATs ("the player dashes 120 px" here, the physics call in the FEAT).
     Optional vision sections: Pillars, Core loop, Direction and References stay only when sdd.vision_sections lists
     them (the game preset lists all four); sdd-constitution deletes the others and adds any other heading the key
     lists after References, so a game's own shape is a section list (a turn-based game adds Combat model, a
     platformer Movement and camera). -->

## Vision

[3 lines: what the game is, for which players, the fantasy that makes it different.]

## Pillars
<!-- Optional (sdd.vision_sections). Design pillars: three to five player experiences that every NEED serves, each
     with the work it rules out. A NEED names the pillar it serves (Triage, Pillar: P<n>); sdd-specify parks or
     rejects one that serves none, citing this table, and sdd-check C13 flags it. Ids are never reused. -->

| Id | Pillar | Rules out |
|---|---|---|
| P1 | [an experience in the player's words: "Every battle effect says why on screen"] | [the kind of work it refuses] |

## Core loop
<!-- Optional (sdd.vision_sections). What the player repeats, as actions, feedback and rewards: the moment-to-moment
     loop and the session loop around it. -->

- Moment to moment: [action → feedback → reward → next goal]
- Session: [why the player starts a session, what they leave with, why they come back]

## Direction
<!-- Optional (sdd.vision_sections). Art, camera, audio and feel in a few lines, each with the approved mock, capture
     or reference that holds it. -->

- Art: [style, palette, sprite or model scale — approved mock path]
- Camera: [view, zoom, what stays on screen]
- Audio: [music and effects mood]
- Feel: [pacing, input response, the feedback every action gets]

## References
<!-- Optional (sdd.vision_sections). Games and works this one learns from: what it takes and what it leaves. -->

| Reference | Take | Leave |
|---|---|---|
| [game or work] | [what to follow] | [what not to] |

## First-delivery scope
<!-- Counted: every item carries a number (regions, maps, characters, items, quests, screens), so a NEED is checked
     against it. -->

| Item | Count |
|---|---|
| [regions, maps, characters, items, quests or screens] | [n] |

## Out of scope (explicit)
<!-- One line per refused or deferred mode, system or content, with why and until when. sdd-specify closes a NEED
     that hits a line rejected (never) or parked (later), citing the line; sdd-check C13 flags it. -->

- [mode, system or content — why; never | after <milestone>]

## Glossary
<!-- sdd-constitution seeds it; sdd-clarify adds each domain term a REQ uses. Domain terms only: the kit defines the
     process terms (NEED, REQ, FEAT, decision, debt). -->

| Term | Definition | Source |
|---|---|---|
| [Term] | [1 sentence] | [doc/legacy/decision] |

## Architecture
<!-- sdd-constitution. The base architecture in one line with the decision that records it, then one row per area: a
     part of the code a change is counted against (sdd-tasks sizes a task row by the areas it touches; sdd-plan places
     the design in them). -->

[Base architecture in one line, for example "authoritative server, thin client" — DEC-nnn.]

| Area | Paths | Holds |
|---|---|---|
| [area] | [rooted folder or glob] | [what lives there, one line] |

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
