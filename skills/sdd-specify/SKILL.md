---
name: sdd-specify
version: "1.0"
description: SDD step 1 — turns a feature description into FEAT-nnn (the what and why, not the how) and its linked REQ-F/REQ-NF, with testable acceptance criteria. Use when starting any new feature. Do not use to refine an existing FEAT (skill sdd-clarify) or to record a technical decision alone (DEC via sdd-plan).
argument-hint: "<feature description in natural language>"
triggers:
  - user
allowed-tools:
  - read
  - glob
  - grep
  - write
  - exec
---

# SDD 1 — Specify

Process reference: `../sdd-constitution/references/sdd-process.md`.

Templates: `../../templates/spec-feature.md`, `../../templates/spec-requirement-functional.md`, `../../templates/spec-requirement-non-functional.md`.

## Steps

1. Next number: `ls docs/spec/features | sort | tail -1`. Never reuse.
2. Read `docs/spec/spec.md` (scope, glossary) and existing features: does the feature already exist, collide with, or depend on another? Record under *Relations*.
3. Write `FEAT-nnn-slug.md`:
   - **Problem/value** for the player/user (the why).
   - Explicit **Scope** and **Out of scope**.
   - **Acceptance criteria** in Given/When/Then format, each verifiable by an automated test or a reproducible step. Minimum: 1 happy path, 1 sad path.
   - **Linked requirements**: create new `REQ-F-*` (behavior) and `REQ-NF-*` (performance, security, compatibility) or reference existing ones. Each requirement = 1 file, 1 testable sentence.
   - **Open questions** marked `[NEEDS CLARIFICATION: ...]` — maximum 5; beyond that the request is too big: propose splitting it.
   - **No** technical decisions (framework, table, message). That is `sdd-plan`.
4. Frontmatter: `id`, `title`, `status: proposed`, `requirements: [...]`, `flag: null`, `card: null`, `created`.
5. Update the index in `spec.md`.
6. Validate: `platforms/tools/check.sh --spec docs/spec` (schemas).

## Completion criteria

- Every acceptance criterion answers "which test proves this?".
- No orphan requirement (no FEAT) and no FEAT without a requirement.
- Claims classified (`[FACT]`/`[HYPOTHESIS]`/...).
