---
id: FEAT-000
title: "[Short infinitive title: Validate a FEAT with no REQ]"
status: proposed
issue: ""
pr: ""
created: "YYYY-MM-DD"
updated: "YYYY-MM-DD"
---
<!-- The FEAT of the FEAT-only flow (sdd.flow: feat-only, the tooling preset; KIT-100), created by sdd-plan from the
     request itself: no NEED and no REQ. The project's rules, skills and code are its spec, so the acceptance criteria
     hold this delivery's rules, each with the command that proves it. The id takes sdd.id_prefix.feature (FEAT, or a
     project's own such as KIT). One FEAT is one item: one issue and one PR (pr_unit: feat), and with
     sdd.task_table: false it has no ## Tasks table. Under sdd.record_when: big-change only a big change gets one.
     status: proposed while sdd-plan drafts it, planned after a clean full-scope sdd-check; then spec_trace.py
     sync-status derives it from its PR (`pr`, else the PR whose body closes `issue`): in-progress while that PR is
     open, delivered once it merges, each with its History line (`pr: delivered (<repo>#N merged)`); sdd-plan writes
     cancelled with the reason. Never edit status by hand.
     Register (skills/sdd-constitution/references/sdd-process.md, Register): technical documentation, the files that
     change and the commands that prove them. -->

# FEAT-000 — [Title]

## Problem and evidence

[FACT] [What is wrong or missing, with the reproduction: repository, issue or PR, command and its output.]

## Scope

- [Each file that changes and what it gains; a rule line quoted exactly.]

## Out of scope

- [What this delivery leaves out, and where it goes.]

## Acceptance criteria
<!-- The rules of this delivery. Each row names the command whose output proves it; sdd-check C8 reads every Scope
     line against a row and every row against its Proof. There is no Proves column: there are no REQs. -->

| ID | Given | When | Then | Proof |
|---|---|---|---|---|
| CA-1 | [initial state] | [action] | [observable result] | `[command]` |
| CA-2 | [sad path: invalid input, a refused value] | | | |

## Plan
<!-- filled by sdd-plan: one ### section per name in sdd.plan_sections, in this order (the tooling preset: Tests and
     Risks); each holds its content or one line "— <why it does not apply>". -->

### Tests

### Risks

## Decisions
<!-- one line per choice the spec did not fix: YYYY-MM-DD (<PR>): chose X over Y because Z. -->

## History

- YYYY-MM-DD plan: created from the request ([issue or chat]).
