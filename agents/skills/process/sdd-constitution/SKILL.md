---
name: sdd-constitution
version: "1.0"
description: SDD step 0 — creates (or reviews) the project constitution - the repo's AGENTS.md with verifiable principles and docs/spec/spec.md with vision, scope, glossary and index. Use once per new project, or when principles change.
argument-hint: "[product description and stack, or 'review']"
triggers:
  - user
allowed-tools:
  - read
  - glob
  - grep
  - write
  - edit
  - exec
---

# SDD 0 — Constitution

Reference: `agents/skills/process/README.md`. Templates: `agents/templates/project-agents-*.md`, `agents/templates/spec-index.md`.

## Prerequisites

- Repo initialized. If `AGENTS.md` or `docs/spec/` already exist, **do not overwrite**: read and propose a diff.
- Stack decisions already made by the product (language, engine, database). If missing, ask — it is a product decision.

## Steps

1. Read the README, folder structure, manifests (`pom.xml`, `project.godot`, `compose.yml`) — what the agent **cannot infer** is what goes into `AGENTS.md`.
2. Pick the closest project template; fill `[brackets]` only with verified facts (actually installed/pinned versions). No fact → `[HYPOTHESIS: ...]`.
3. Repo `AGENTS.md`: ≤150 lines. Sections: Stack · Commands · Structure · Patterns (condition→action) · Boundaries (Always/Ask/Never) · Sessions (how to record progress) · Where the rest lives. The kit's global rules are **not** repeated here.
4. `docs/spec/spec.md` from the template: vision (3 lines), explicit out-of-scope, initial glossary, empty indexes.
5. Create folders `features/ requirements/functional requirements/non-functional decisions/ debts/` with `.gitkeep`.
6. If the product brought already-made decisions → one `DEC-nnn` per decision with state `approved` and the source (who/when).

## Completion criteria

- `AGENTS.md` passes: does each line change a behavior? is there a real build/test command executed at least once (`[FACT]`)?
- `spec.md` validates against `platforms/ci/schemas/spec.schema.json`.
- Nothing invented: versions, commands and paths exist.

## Do not

- Copy generic kit rules into the repo.
- Fix numeric targets (players, latency) without a hypothesis and a measurement method.
