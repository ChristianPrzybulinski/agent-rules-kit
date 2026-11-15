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
<!-- Created by sdd-plan from a refined NEED: a FEAT is one delivery, the technical package that implements approved REQs.
     status: proposed while sdd-plan drafts it, planned after a clean full-scope sdd-check; in-progress, validated and
     delivered are derived from GitHub by tooling; clarified remains only on FEATs written before the NEED flow. Never
     edit status by hand. -->

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
<!-- filled by sdd-plan -->

## Tasks
<!-- filled by sdd-tasks; State is derived from the task issue (merged PR = done) and never edited by hand -->

| ID | Task | Files | Proof of completion | Covers | Depends on | State | Complexity | Model | Wave |
|---|---|---|---|---|---|---|---|---|---|

## Decisions
<!-- one line per choice the spec did not fix, written when its task closes: YYYY-MM-DD T<n> (<PR>): chose X over Y because Z. New [DECISION] lines of this spec go here; Open questions keeps only open questions. The action log stays in the PR body. -->

## Audit
<!-- filled by the calling session from the sdd-check report (or a FEAT-000.checklist.md file) -->

## History

- YYYY-MM-DD plan: created from NEED-nnn.
