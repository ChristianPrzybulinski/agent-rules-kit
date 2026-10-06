---
id: J-00
title: "[Journey title: <actor> <does what>, one user-visible flow]"
status: proposed
owner: "[product]"
created: "YYYY-MM-DD"
updated: "YYYY-MM-DD"
---

# J-00 — [Title]

## Goal

[FACT] Who does what, end to end, in one user-visible flow. [Name the stage or milestone it covers.]

## Preconditions

- [FACT] [what must already hold: earlier journeys' artifacts, services running, fixtures in place]

## Steps

| Step | Actor action → visible result | Rules | Implemented by | Proven by |
|---|---|---|---|---|
| S1 | [actor starts … → sees …] | — | FEAT-nnn Tn | `clone-name/tests/**` |
| S2 | [actor … → …] | REQ-F-nnn | FEAT-nnn Tn · FEAT-nnn Tn | `clone-name/tests/**` · FEAT-nnn Tn · manual: [check] |

## Alternative paths

| Step | At | Actor action → visible result | Rules | Implemented by | Proven by |
|---|---|---|---|---|---|
| A1 | S1 | [failure or variant → result] | REQ-F-nnn | FEAT-nnn Tn | `clone-name/tests/**` |

## Prerequisites

| Step | What the steps need | Implemented by |
|---|---|---|
| P1 | [contracts, generated assets, tooling — nothing the user sees] | FEAT-nnn Tn |

## Out of this journey

- [FACT] [adjacent flow and where it is covered — another journey, or never]

## History

- YYYY-MM-DD: created.

<!-- Notes the checker (spec_trace.py) enforces:

  - Step ids: S<n> main path (in order), A<n> alternative (its `At` names the main step it diverts
    from), P<n> prerequisite. A first header cell `Step` marks a step table.
  - `Rules` cites REQ ids only — never rule values or free text. A rule a journey exercises is
    promoted to a REQ-F in the same PR; a rule no journey uses stays FEAT-local.
  - `Implemented by` cites `FEAT-nnn Tn` task rows only, as they exist on main.
  - `Proven by` holds `FEAT-nnn Tn` test tasks, backticked paths rooted at a clone name
    (`clone-name/path/**`), and an optional trailing `manual: <check>`. Paths rooted at the spec's
    own repository must match a file in it.
  - Every link is written once: in the journey (journey → rule, task, test) or in FEAT/REQ
    frontmatter (FEAT ↔ REQ). The traceability matrix is generated — never edited by hand.
-->
