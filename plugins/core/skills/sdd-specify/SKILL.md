---
name: sdd-specify
description: SDD step 1 — feature and requirement specification. Use when a described feature needs FEAT/REQ criteria. Not for open questions (skill sdd-clarify).
argument-hint: "<feature description in natural language>"
triggers:
  - user
disable-model-invocation: true
allowed-tools:
  - read
  - glob
  - grep
  - edit
  - exec
---

# SDD 1 — Specify

Process: `../sdd-constitution/references/sdd-process.md`. Templates: `../../templates/spec-feature.md`, `../../templates/spec-requirement-functional.md`, `../../templates/spec-requirement-non-functional.md`.

## 1. Qualify the input

If the idea is still vague or the user wants it stress-tested, run `/grilling` first. Start this step when the problem/value and intended user can be described without choosing implementation.

## 2. Select identifiers

Read `docs/spec/spec.md` and existing features. Choose the next unused `FEAT-nnn`; record collisions, dependencies and related features rather than duplicating them.

## 3. Write the feature

Create `FEAT-nnn-slug.md` with:

- problem/value, explicit scope and out-of-scope;
- Given/When/Then criteria with at least one happy and one sad path;
- linked `REQ-F-*` behavior and `REQ-NF-*` quality requirements, one testable sentence per file;
- at most five `[NEEDS CLARIFICATION: ...]` questions; split the feature if more are needed;
- no framework, table or message choice—those belong to planning.

Set `status: proposed`, requirements, `flag: null`, `card: null` and creation date; update the feature/requirement indexes.

## 4. Validate

Run `platforms/tools/check.sh --spec docs/spec`. Every criterion must name an automated test or reproducible proof, and every requirement must be linked from a feature.

Done when: a described feature has valid FEAT/REQ files, happy/sad criteria, classified claims and no implementation decision.
