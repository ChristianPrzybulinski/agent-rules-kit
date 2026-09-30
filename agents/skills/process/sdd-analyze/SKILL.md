---
name: sdd-analyze
version: "1.0"
description: SDD step 3 — consistency analysis across FEAT, REQs, DECs, plan and tasks - contradictions, gaps, orphan requirements, criteria without a task, tasks without a criterion. Read-only; produces a report. Use after clarify and after plan/tasks.
argument-hint: "FEAT-nnn | all"
triggers:
  - user
  - model
allowed-tools:
  - read
  - glob
  - grep
---

# SDD 3 — Analyze

Read-only. Does not edit specs; the report goes to the chat (and optionally `docs/spec/reports/analyze-YYYYMMDD.md` if the user asks).

## Checks

| # | Check | Severity |
|---|---|---|
| A1 | REQ referenced in the FEAT exists as a file; every REQ file is referenced by ≥1 FEAT | high |
| A2 | Acceptance criterion contradicts another criterion or a REQ (e.g.: "no login" vs auth REQ) | critical |
| A3 | FEAT depends on a FEAT with a lower status (planning on what was not clarified) | high |
| A4 | Term used is not in the `spec.md` glossary | low |
| A5 | Vague quantifier with no number and no `[HYPOTHESIS]` | medium |
| A6 | Claim without `[FACT]/[DECISION]/[PROPOSAL]/[HYPOTHESIS]/[BLOCKER]` classification | medium |
| A7 | (if there is a plan) technical decision in the plan without a `DEC` when an alternative was rejected | medium |
| A8 | (if there are tasks) acceptance criterion with no covering task; task with no criterion | high |
| A9 | Plan violates a kit/repo rule (e.g.: Redis as source of truth; Gradle; framework in the domain) | critical |
| A10 | Invalid frontmatter against `platforms/ci/schemas/` | high |

## Report

```
Scope: FEAT-nnn | all
| # | Severity | Where (file:line) | Problem | Suggestion |
Summary: N critical, M high, ...
Blocks moving to <next step>? YES (critical/high) | NO
```

Critical or high → do not proceed to `plan`/`implement` until resolved (via `clarify` or spec edit).
