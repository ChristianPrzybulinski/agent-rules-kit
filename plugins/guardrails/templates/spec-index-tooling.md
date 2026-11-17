---
project: "[project-name]"
version: "0.1.0"
updated: "YYYY-MM-DD"
# No sdd: block. A tooling project's process parameters come from its .ai-kit.yaml: project.kind: tooling gives the
# FEAT-only flow (profile.schema.json, x-presets), and a key written here would override that preset (KIT-100).
---

# [Project name] — Specification

Index of a tool repository that runs the FEAT-only flow (`sdd.flow: feat-only`): no NEED, no REQ and no journey. The
tool's own rules, skills and code are its spec; each FEAT under `features/` records one big change (template
`spec-feature-lite.md`), its acceptance criteria and their proof commands, and its status follows its PR. Classify
claims: `[FACT]` `[DECISION]` `[PROPOSAL]` `[HYPOTHESIS]` `[BLOCKER]`.

<!-- The spec.md template of project.kind tooling (init-spec.sh copies it; spec-index-business.md and
     spec-index-game.md are the others). Register (skills/sdd-constitution/references/sdd-process.md, Register):
     one paragraph on what the tool is, then the indexes. -->

## Features

| ID | Title | Status | PR |
|---|---|---|---|

## Decisions

| ID | Title | Status |
|---|---|---|
