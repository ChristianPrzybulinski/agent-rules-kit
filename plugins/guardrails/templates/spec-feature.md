---
id: FEAT-000
title: "[Short infinitive title: Authenticate player]"
status: proposed
requirements: []
depends_on: []
scope: []
milestone: null
evidence: []
flag: null
card: null
owner: "[product]"
created: "YYYY-MM-DD"
updated: "YYYY-MM-DD"
---
<!-- Created by sdd-plan from a refined NEED, or from the request itself under sdd.needs: false: a FEAT is one delivery,
     the technical package that implements approved REQs, never a bucket for later work; work that exceeds
     sdd.max_feat_tasks rows is split into several FEATs.
     status: proposed while sdd-plan drafts it, planned after a clean full-scope sdd-check; in-progress is derived once a
     task row is doing or done (the rows follow their items: GitHub issues, or TASK files with tracker: none), and
     status --write records that move in History whichever row moved it;
     validated is written by sdd-review and delivered by sdd-release (or sdd-review under release: merge), through
     spec_trace.py with their History line; clarified remains only on FEATs written before the NEED flow. Never
     edit status by hand.
     Register (skills/sdd-constitution/references/sdd-process.md, Register): technical documentation: Plan, contracts,
     data, assets and tasks, with links to the functional layer; it cites a REQ and never restates its rule. -->

# FEAT-000 — [Title]

## Problem / value

[One line, then the NEED it delivers: `NEED-nnn`. The full problem, Situations and scope live in the NEED.]

## Scope

- [the REQs this delivery implements, new or amended: `REQ-F-nnn`]

## Out of scope

- [REQs or parts left to another FEAT, and which]

## Acceptance criteria
<!-- Technical: what the delivery's tests prove (contract, unit, integration, e2e). The functional criteria are the REQs'
     Verification; each row cites the REQ ids it proves, and every REQ in Scope is proved by at least one row. -->

| ID | Given | When | Then | Test type | Proves |
|---|---|---|---|---|---|
| CA-1 | [initial state] | [action] | [observable result] | unit / integration / contract / e2e | REQ-F-000 |
| CA-2 | [sad path: invalid input / no permission / timeout] | | | | REQ-F-000 |

## Linked requirements

- `REQ-F-000` — [title]
- `REQ-NF-000` — [title]

## Relations

- Depends on: [FEAT-xxx or —]
- Conflicts/overlaps: [—]
- Related legacy: [path in the archive, if any — `[FACT]` only if verified]
- Evidence: [frontmatter `evidence` IDs → `docs/legacy/evidence.md#e01`]

## Open questions

- [NEEDS CLARIFICATION: ...]

## Plan
<!-- filled by sdd-plan: one ### section per name in spec.md sdd.plan_sections, in this order (Risks and Tests always);
     each holds its content or one line "— <why it does not apply>". Task cells point to "Plan § <section>". -->

### Design

### Contract

### Data

### UI

### Flag

### Tests

### Observability

### Risks

### Dependencies

## Tasks
<!-- filled by sdd-tasks in a spec PR, cut once approved or merged. Status (todo, doing, blocked, done, cancelled) is derived
     from the item (GitHub issue, or TASK-nnn file with tracker: none) and never edited by hand; Item is — until the cut. -->

| ID | Task | Files | Proof of completion | Covers | Depends on | Status | Complexity | Model | Wave | Item |
|---|---|---|---|---|---|---|---|---|---|---|

## Decisions
<!-- one line per choice the spec did not fix, written when its task closes: YYYY-MM-DD T<n> (<PR>): chose X over Y because Z. New [DECISION] lines of this spec go here; Open questions keeps only open questions. The action log stays in the PR body. -->

## Audit
<!-- filled by the calling session from the sdd-check report (or a FEAT-000.checklist.md file) -->

## Closure
<!-- written by sdd-review on main after the last row merges, before spec_trace.py validate: Main commit, rows for the
     task proofs, the lint, the broad suite, each REQ-NF measurement and the missing-test rows filed, outcome, retro -->

## History

- YYYY-MM-DD plan: created from NEED-nnn.
