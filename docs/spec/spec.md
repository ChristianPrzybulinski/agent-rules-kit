---
project: "agent-rules-kit"
version: "1.0.0"
updated: "2026-11-22"
# No sdd: block. The kit's process parameters come from its .ai-kit.yaml: project.kind: tooling gives the FEAT-only
# flow (profile.schema.json, x-presets), and a key written here would override that preset (KIT-100).
---

# agent-rules-kit — Specification

Index of the kit's own FEAT-only flow (`sdd.flow: feat-only`, KIT-101): no NEED, no REQ and no journey. The kit's
rules, skills, templates and tools are its spec; each FEAT under `features/` (`KIT-nnn.md`, template
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
| [KIT-102](features/KIT-102.md) | Split the red check into a plan and a judge of given sides | delivered | #379 |
| [KIT-103](features/KIT-103.md) | Name every spec record file by its id alone | delivered | #384 |
| [KIT-104](features/KIT-104.md) | Route a finding where it is found; a NEED only for a need or an owner decision | delivered | #397 |
| [KIT-105](features/KIT-105.md) | File closeout kit proposals directly as GitHub issues | delivered | #395 |
| [KIT-106](features/KIT-106.md) | Track each FEAT in one GitHub issue | delivered | #399 |
| [KIT-107](features/KIT-107.md) | Leave generated output out of the red check's code roots | delivered | #402 |
| [KIT-108](features/KIT-108.md) | A retired REQ needs no FEAT | delivered | #403 |
| [KIT-109](features/KIT-109.md) | Fail a CHANGELOG line added under a released version | delivered | #404 |
| [KIT-112](features/KIT-112.md) | Read each OWNER/NAME#N issue in its own repository | delivered | #408 |
| [KIT-113](features/KIT-113.md) | Let an unanswered owner question wait only at the merge | delivered | #410 |
| [KIT-114](features/KIT-114.md) | Name a plugin agent as <plugin>:<profile> in a skill's agent field | delivered | #414, #418 |
| [KIT-115](features/KIT-115.md) | Warn on sibling task rows and on edges inside a set | delivered | #430 |
| [KIT-116](features/KIT-116.md) | A row that adds an enabler consumer lists both ENB files | delivered | #437 |
| [KIT-117](features/KIT-117.md) | Require an evidenced why chain on fix and improvement PRs, checked as a WARN | delivered | #455 |

## Decisions

| ID | Title | Status |
|---|---|---|
