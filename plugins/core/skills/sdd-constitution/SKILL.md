---
name: sdd-constitution
description: SDD step 0 — project constitution and spec index. Use when starting a project or changing principles. Not for one feature (skill sdd-specify).
argument-hint: "[product description and stack, or 'review']"
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

# SDD 0 — Constitution

Process: `references/sdd-process.md`. Templates: `../../templates/spec-index.md` and `../../templates/project-agents-*.md`.

## 1. Inspect before creating

Read the README, repository structure and stack manifests. If `AGENTS.md` or `docs/spec/` exists, review and propose a diff instead of overwriting it. Ask for missing product choices such as language, engine or database.

## 2. Write the project constitution

- Select the closest project template and replace placeholders only with verified versions, commands and paths.
- Keep repository `AGENTS.md` within 150 lines: Stack, Commands, Structure, condition→action Patterns, Always/Ask/Never boundaries, Sessions and pointers to detail.
- Add one line to `AGENTS.md` naming the spec regimes: which `docs/spec` artifacts are spec-anchored (maintained) and that FEAT/task status is derived, never typed.
- Do not copy the kit's global rules into the project.

## 3. Initialize the spec

Create `docs/spec/spec.md` with a three-line vision, explicit out-of-scope, glossary and empty FEAT/REQ/DEC/DEBT indexes. Create `features/`, `requirements/{functional,non-functional}/`, `decisions/` and `debts/`.

Declare the two regimes in `spec.md` (see `references/sdd-process.md`, Regimes): spec-anchored for contracts, decisions, requirements, journeys and the index; spec-first for FEAT bodies and task tables.

## 4. Record existing decisions

For an already-approved product decision, create one decision record (`DTEC-nnn`/`DGME-nnn`/`DPRO-nnn` per kind) with `status: approved` and its source. Unknown numeric targets remain hypotheses with a measurement method.

## 5. Validate

Run the project spec validator and one real build/test command. Mark only observed commands and versions as facts.

Done when: project principles change behavior, `spec.md` validates, required folders exist, and no version, command, path or target was invented.
