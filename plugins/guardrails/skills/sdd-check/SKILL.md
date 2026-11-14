---
name: sdd-check
description: SDD step 3 — read-only check, functional (NEED) or technical (FEAT). Use when a NEED or a FEAT needs gap checks. Not for ambiguity (skill sdd-clarify).
argument-hint: "NEED-nnn | FEAT-nnn | all [validator=<output of check_spec.py 2>&1>] [trace=<output of spec_trace.py check 2>&1>]"
triggers:
  - user
  - model
agent: researcher
context: fork
background: false
allowed-tools:
  - read
  - glob
  - grep
---

# SDD 3 — Check

Process: `../sdd-constitution/references/sdd-process.md`. Read-only: this step edits no specification. Checklist: `references/check-list.md`.

Two modes, chosen by the argument:
- functional (`NEED-nnn`, run by `sdd-clarify` before `refined`): the NEED, its REQs, journeys and product decisions; rows C1, C2, C4, C5, C6, the journey links and checklist Q1–Q7; a block stops `refined`.
- technical (`FEAT-nnn`, run by `sdd-plan` before `planned`): the FEAT, its Plan, Tasks and decisions; rows C3, C7, C8, C9, C10 and checklist Q8–Q11; a block stops `sdd-tasks`. `all` runs both on every artifact.

## 1. Mechanical checks

a. Validator verdict. The calling session runs `python3 .github/spec-lint/check_spec.py docs/spec .github/spec-lint/schemas 2>&1` (the project copy synced from the kit `check_spec.py`) and pastes the whole output after `validator=`, because the `researcher` profile has no `exec`. Success is the single line `spec: OK (N artifacts)`; failures are `FAIL: ...` lines on stderr, hence `2>&1`. With no `validator=` argument, finding #1 is `high | validator not run; run <command>`. Every pasted `FAIL:` line becomes one `high` finding.

b. Journey links (functional mode, when the project keeps `docs/spec/journeys/`). The calling session pastes `spec_trace.py check 2>&1` after `trace=`; each failure line is one `high` finding, and a missing `trace=` is `high | journey check not run`.

c. Consistency table. Load the artifacts of the mode, then check its rows:

| Id | Check | Severity |
|---|---|---|
| C1 | missing FEAT↔REQ or NEED→REQ link, orphan requirement, or a NEED Situation with no Refinement row | high |
| C2 | contradictory criteria/requirements | critical |
| C3 | dependency on a lower-status feature | high |
| C4 | undefined glossary term | low |
| C5 | vague unmeasured quantity | medium |
| C6 | unclassified claim | medium |
| C7 | rejected alternative without DEC | medium |
| C8 | REQ in Scope with no criterion proving it, criterion without task, or task without criterion | high |
| C9 | plan violating kit/repository rule | critical |
| C10 | invalid frontmatter | high |

## 2. Judgment checks

Grade every item of `references/check-list.md` that the mode covers (functional Q1–Q7, technical Q8–Q11) pass / fail / not-applicable with a `path:line` as evidence. A fail on a security or integrity item is `critical`.

## 3. Report

One format. Line one: `validator: OK (N artifacts) | FAIL (n lines) | not run`. Then `# | step | severity | file:line | problem | suggestion`, counts by severity, and `blocked: yes|no` (critical or high blocks `refined` in functional mode and `sdd-tasks` in technical mode). Save under `docs/spec/reports/` only when requested; the calling session pastes the table into the FEAT `## Audit` section, or the NEED's History as one line with the counts.

## 4. Route findings

Ambiguity goes to `sdd-clarify`, a missing Situation to `sdd-specify`, a plan or task gap to `sdd-plan` or `sdd-tasks`, a kit-rule violation to a decision record or a blocker.

Done when: every finding cites `path:line`, the validator verdict is on line one, and the report states its mode and whether the next status is blocked.
