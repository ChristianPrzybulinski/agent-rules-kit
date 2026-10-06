---
name: sdd-check
description: SDD step 3 — mechanical spec check and quality checklist. Use when a clarified FEAT needs gap checks before planning. Not for ambiguity (skill sdd-clarify).
argument-hint: "FEAT-nnn | all [validator=<output of check_spec.py 2>&1>]"
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

## 1. Mechanical checks

a. Validator verdict. The calling session runs `python3 .github/spec-lint/check_spec.py docs/spec .github/spec-lint/schemas 2>&1` (the project copy synced from the kit `check_spec.py`) and pastes the whole output after `validator=`, because the `researcher` profile has no `exec`. Success is the single line `spec: OK (N artifacts)`; failures are `FAIL: ...` lines on stderr, hence `2>&1`. With no `validator=` argument, finding #1 is `high | validator not run; run <command>`. Every pasted `FAIL:` line becomes one `high` finding.

b. Consistency table. Load the requested FEAT or all features, their requirements/decisions and any Plan/Tasks sections, then check:

| Id | Check | Severity |
|---|---|---|
| C1 | missing FEAT↔REQ link or orphan requirement | high |
| C2 | contradictory criteria/requirements | critical |
| C3 | dependency on a lower-status feature | high |
| C4 | undefined glossary term | low |
| C5 | vague unmeasured quantity | medium |
| C6 | unclassified claim | medium |
| C7 | rejected alternative without DEC | medium |
| C8 | criterion without task or task without criterion | high |
| C9 | plan violating kit/repository rule | critical |
| C10 | invalid frontmatter | high |

## 2. Judgment checks

Grade every item of `references/check-list.md` pass / fail / not-applicable with a `path:line` as evidence. A fail on a security or integrity item is `critical`.

## 3. Report

One format. Line one: `validator: OK (N artifacts) | FAIL (n lines) | not run`. Then `# | step | severity | file:line | problem | suggestion`, counts by severity, and `blocked: yes|no` (critical or high blocks `sdd-plan`). Save under `docs/spec/reports/` only when requested; the calling session pastes the table into the FEAT `## Audit` section.

## 4. Route findings

Ambiguity goes to `sdd-clarify`, artifact corrections to the owning step, a kit-rule violation to a DEC or a blocker.

Done when: every finding cites `path:line`, the validator verdict is on line one, and the report states whether planning is blocked.
