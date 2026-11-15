---
name: sdd-check
description: SDD tool — read-only spec check that sdd-clarify and sdd-plan call. Use when a NEED, a FEAT or the spec needs gap checks. Not for ambiguity (skill sdd-clarify).
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

# SDD tool — Check

Process: `../sdd-constitution/references/sdd-process.md`. Read-only: this tool edits no specification. It is not a step of the chain: `sdd-clarify` and `sdd-plan` call it before their status move, and anyone may run it as an audit. Checklist: `references/check-list.md`.

Scope, chosen by the argument:
- functional (`NEED-nnn`, called by `sdd-clarify` before `refined`): the NEED, its REQs, journeys and product decisions; rows C1, C2, C4, C5, C6, C11, the journey links and checklist Q1 (read against each REQ's Verification), Q2–Q4 and Q7; a block stops `refined`.
- full (`FEAT-nnn`, called by `sdd-plan` before `planned`): the functional scope again on the FEAT's REQs and its NEED, plus the FEAT, its Plan, Tasks once cut and decisions with rows C3, C7, C8, C9, C10 and checklist Q1 (read against the FEAT's criteria), Q5, Q6 and Q8–Q11; a block stops `planned`.
- `all` (an audit): the full scope on every artifact.

## 1. Mechanical checks

a. Validator verdict. The calling session runs `python3 .github/spec-lint/check_spec.py docs/spec .github/spec-lint/schemas 2>&1` (the project copy synced from the kit `check_spec.py`) and pastes the whole output after `validator=`, because the `researcher` profile has no `exec`. Success is the single line `spec: OK (N artifacts)`; failures are `FAIL: ...` lines on stderr, hence `2>&1`. With no `validator=` argument, finding #1 is `high | validator not run; run <command>`. Every pasted `FAIL:` line becomes one `high` finding.

b. Journey links (functional and full scope, when the project keeps `docs/spec/journeys/`). The calling session pastes `spec_trace.py check 2>&1` after `trace=`; each failure line is one `high` finding, and a missing `trace=` is `high | journey check not run`. A step written in `sdd-clarify` holds `—` in `Implemented by` and `Proven by`, which the validator accepts until a FEAT that lists one of the step's REQs is `validated` or `delivered` (`../sdd-clarify/references/journeys.md`), so a NEED's new step does not block `refined`.

c. Consistency table. Load the artifacts of the scope, then check its rows:

| Id | Check | Severity |
|---|---|---|
| C1 | missing FEAT↔REQ (full) or NEED→REQ (functional) link, orphan requirement, or a NEED Situation with no Refinement row | high |
| C2 | contradictory criteria/requirements | critical |
| C3 | dependency on a lower-status feature | high |
| C4 | undefined glossary term | low |
| C5 | vague unmeasured quantity | medium |
| C6 | unclassified claim | medium |
| C7 | rejected alternative without DEC | medium |
| C8 | REQ in Scope with no criterion proving it; criterion without task or task without criterion, once Tasks exist | high |
| C9 | plan violating kit/repository rule | critical |
| C10 | invalid frontmatter | high |
| C11 | a REQ states how instead of what (algorithm, message, table, framework); rule: `../sdd-clarify/references/req-scope.md` | medium |

## 2. Judgment checks

Grade every item of `references/check-list.md` that the scope covers (functional Q1–Q4 and Q7, full Q1–Q11) pass / fail / not-applicable with a `path:line` as evidence. A fail on a security or integrity item is `critical`.

## 3. Report

One format. Line one: `validator: OK (N artifacts) | FAIL (n lines) | not run`. Then `# | step | severity | file:line | problem | suggestion`, counts by severity, and `blocked: yes|no` (critical or high blocks `refined` in the functional scope and `planned` in the full scope). Save under `docs/spec/reports/` only when requested; the calling session pastes the table into the FEAT `## Audit` section, or the NEED's History as one line with the counts.

## 4. Route findings

Ambiguity goes to `sdd-clarify`, a missing Situation to `sdd-specify`, a plan or task gap to `sdd-plan` or `sdd-tasks`, a kit-rule violation to a decision record or a blocker.

Done when: every finding cites `path:line`, the validator verdict is on line one, and the report states its scope and whether the next status is blocked.
