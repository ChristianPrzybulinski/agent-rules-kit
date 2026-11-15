---
project: "[project-name]"
version: "0.1.0"
protocol_version: 1
card_project: null
updated: "YYYY-MM-DD"
# Process parameters, written by sdd-constitution with the kit defaults below; each key, its default and the step
# that reads it: skill sdd-constitution, references/sdd-parameters.md. check_spec.py --params prints the resolved block.
sdd:
  needs: true
  # journeys: absent = on when docs/spec/journeys/ exists
  tracker: github
  plan_sections: [Design, Contract, Data, UI, Flag, Tests, Observability, Risks, Dependencies]
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

## Vision

[3 lines: what it is, for whom, what makes it different.]

## First-delivery scope

- [item]

## Out of scope (explicit)

- [item — and why, if not obvious]

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
