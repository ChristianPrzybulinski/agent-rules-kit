---
name: sdd-triage
description: "SDD triage — classify a NEED-nnn, set its priority and route it. Use when a NEED is proposed. Not for describing scope (skill sdd-specify)."
argument-hint: "NEED-nnn"
triggers:
  - user
  - model
allowed-tools:
  - read
  - glob
  - grep
  - edit
  - exec
---

# SDD triage

Decides what a proposed NEED is and where it goes: `status: triaged`, or closed `routed`, `merged`, `rejected` or `parked`. It decides only: it never fills Desired outcome, Situations, Scope, Out of scope or Constraints, which `sdd-specify` fills at the start of refinement. Process: `../sdd-constitution/references/sdd-process.md`.

## 1. Read

- Read `docs/spec/spec.md` and only the REQs, journeys and FEATs the NEED touches; look in `docs/spec/needs/` for a NEED with the same request.

## 2. Classify

First match wins:

| Type | Rule | Route |
|---|---|---|
| fix | a REQ, journey or decision already states the right behavior and the code does not | `routed`: a fix task row cites that artifact and the origin |
| content | only data changes, no rule | `routed`: the project's data-change flow |
| decision | a choice with nothing to deliver | `refine` to a decision record only |
| improvement | changes behavior an existing REQ or journey describes | `refine`: the REQ or journey changes |
| new | no REQ or journey covers it | `refine` |
| platform | process, tooling, CI or the kit | `refine` in the project's platform track |

- A problem with no artifact stating the right behavior is an improvement, never a fix.
- A duplicate closes `merged`, naming the NEED kept; a refused NEED closes `rejected` with its reason.

## 3. Decide

- Complete Problem / value. Fill the Triage block: type and why, existing artifacts touched (with paths), Route, Size (`S`, `M` or `L`, no duration without a measured run) and Priority (`now`, `next` or `later`; `later` closes `parked`, which returns to `triaged` when taken up).
- Finding facts is the agent's job. Open with a verdict and its evidence, then ask one question at a time with two to four options and a recommendation. A vague idea is stress-tested with `/grilling`; a feel question (motion, camera, feedback, UI) gets an `sdd-spike`, whose report becomes Evidence.
- Product confirms a `new`, `improvement`, `platform` or `decision` NEED, a `content` value, a rejection and a park: `Confirmed by: <name>, YYYY-MM-DD`.
- The agent routes a `fix` that cites the violated artifact's path and a duplicate that names the NEED kept, and records `Confirmed by: agent (fix|duplicate), product reviews later`.

## 4. Close

- Set the status, add the History line `YYYY-MM-DD triage: <type>, <route>, <priority>`, run the project spec validator and paste its literal output.
- `refine` hands off to `sdd-specify`; a routed NEED names the fix row or data change that took it.

## Rules

- Never write a REQ, FEAT, decision, debt or task row here, and never fill the sections refinement owns.
- Links are written only in the NEED.

Done when: the NEED validates, Triage names type, route, size, priority and who confirmed, and a closed NEED says where the work went or why it stopped.
