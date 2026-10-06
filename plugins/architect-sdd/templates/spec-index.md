---
project: "[project-name]"
version: "0.1.0"
protocol_version: 1
card_project: null
updated: "YYYY-MM-DD"
---

# [Project name] — Specification

Cover and index. The source of truth for each subject lives in the linked files; here only vision, scope and indexes. Classify claims: `[FACT]` `[DECISION]` `[PROPOSAL]` `[HYPOTHESIS]` `[BLOCKER]`.

Regimes: spec-anchored (maintained and validated for the life of the product) = protocol schemas and examples, content schemas, decisions, requirements, journeys (where the project has them) and this index.
Spec-first (written to cut the work, then frozen as history) = FEAT bodies and task tables; their status is derived by tooling from merged PRs, never edited by hand.

## Vision

[3 lines: what it is, for whom, what makes it different.]

## First-delivery scope

- [item]

## Out of scope (explicit)

- [item — and why, if not obvious]

## Glossary

| Term | Definition | Source |
|---|---|---|
| [Term] | [1 sentence] | [doc/legacy/decision] |

## Reading order for a new session

1. `AGENTS.md`
2. This file
3. `decisions/` with status `approved`
4. The `FEAT` in progress (status `in-progress`, derived)

## Indexes

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
