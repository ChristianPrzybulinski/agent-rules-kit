---
project: "agent-rules-kit"
version: "1.0.0"
updated: "2026-11-17"
# No sdd: block. The kit's process parameters come from its .ai-kit.yaml: project.kind: tooling gives the FEAT-only
# flow (profile.schema.json, x-presets), and a key written here would override that preset (KIT-100).
---

# agent-rules-kit — Specification

Index of the kit's own FEAT-only flow (`sdd.flow: feat-only`, KIT-101): no NEED, no REQ and no journey. The kit's
rules, skills, templates and tools are its spec; each FEAT under `features/` (`KIT-nnn-slug.md`, template
`spec-feature-lite.md`) records one big change as `../features/README.md` defines it, with its acceptance criteria
and their proof commands, and its status follows its PR (`spec_trace.py sync-status`). The records up to KIT-101 stay
in `../features/` in their own format. Classify claims: `[FACT]` `[DECISION]` `[PROPOSAL]` `[HYPOTHESIS]`
`[BLOCKER]`.

<!-- Copied from plugins/guardrails/templates/spec-index-tooling.md (KIT-101). Register
     (plugins/guardrails/skills/sdd-constitution/references/sdd-process.md, Register): one paragraph on what the tool
     is, then the indexes. -->

## Features

| ID | Title | Status | PR |
|---|---|---|---|
| [KIT-102](features/KIT-102-red-check-two-phase.md) | Split the red check into a plan and a judge of given sides | planned | — |

## Decisions

| ID | Title | Status |
|---|---|---|
