---
name: sdd-analyze
description: SDD step 3 — cross-artifact consistency report. Use when FEAT/REQ/DEC/plan/tasks need gap checks. Not for spec quality (skill sdd-audit).
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

Process: `../sdd-constitution/references/sdd-process.md`. This step is read-only; it edits no specification.

## 1. Select the artifact graph

Load the requested FEAT or all features, linked requirements/decisions and any Plan/Tasks sections. Validate frontmatter before comparing content.

## 2. Check consistency

| Check | Severity |
|---|---|
| missing FEAT↔REQ link or orphan requirement | high |
| contradictory criteria/requirements | critical |
| dependency on a lower-status feature | high |
| undefined glossary term | low |
| vague unmeasured quantity | medium |
| unclassified claim | medium |
| rejected alternative without DEC | medium |
| criterion without task or task without criterion | high |
| plan violating kit/repository rule | critical |
| invalid frontmatter | high |

## 3. Report evidence

Produce `# | severity | file:line | problem | suggestion`, counts by severity and whether the next SDD step is blocked. Save under `docs/spec/reports/` only when requested.

## 4. Route findings

Critical/high findings block planning or implementation. Route ambiguity to `sdd-clarify`, quality gaps to `sdd-audit`, and artifact corrections to the owning step.

Done when: every finding cites an artifact location, contradictions/orphans are counted, and the report states whether progression is blocked.
