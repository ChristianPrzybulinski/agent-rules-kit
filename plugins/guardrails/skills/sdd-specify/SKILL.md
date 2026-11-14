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

Start from a `NEED-nnn` with `status: triaged` and route `refine` (skill `sdd-triage`); a request with no NEED goes to `sdd-intake` first. With product, first fill the NEED's Desired outcome, Situations (at least one that goes right and one that goes wrong), Scope, Out of scope, Constraints and Evidence; they are the input, and implementation is still not chosen.

## 2. Select identifiers

Read `docs/spec/spec.md` and existing features. Choose the next unused `FEAT-nnn` — or, when the session prompt reserves a block, the first unused id of that block; the same applies to the `REQ` ids you create. Record collisions, dependencies and related features rather than duplicating them.

## 3. Write the feature

Create `FEAT-nnn-slug.md` with:

- problem/value, explicit scope and out-of-scope;
- Given/When/Then criteria with at least one happy and one sad path;
- linked `REQ-F-*` behavior and `REQ-NF-*` quality requirements, one testable sentence per file;
- at most five `[NEEDS CLARIFICATION: ...]` questions; split the feature if more are needed;
- no framework, table or message choice—those belong to planning.

Set `status: proposed`, requirements, `flag: null`, `card: null` and creation date; update the feature/requirement indexes.

In the NEED, add the new FEAT and REQ ids to `features` and `requirements`, one Refinement row per Situation (what it became and why) and a History line.

## 4. Validate

Run the project spec validator (`python3 .github/spec-lint/check_spec.py docs/spec .github/spec-lint/schemas`; in this kit, `platforms/tools/check.sh --spec docs/spec`). Every criterion must name an automated test or reproducible proof, and every requirement must be linked from a feature.

Done when: a described feature has valid FEAT/REQ files, happy/sad criteria, classified claims and no implementation decision.
