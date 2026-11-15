---
name: sdd-specify
description: "SDD 1 — specify a NEED-nnn: decide type, route and priority, then describe. Use when a NEED is proposed or taken up. Not for writing REQs (skill sdd-clarify)."
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

# SDD 1 — Specify

Specifies a NEED in two parts: decide (`proposed` → `triaged`, or closed) and describe (`triaged` → `specified`). It never writes a REQ, FEAT, decision, debt or task row. Process: `../sdd-constitution/references/sdd-process.md`. Template: `../../templates/spec-need.md`. A request with no NEED goes to `sdd-intake` first.

## 1. Decide (after intake, now or later; a recorded NEED may wait)

Read `docs/spec/spec.md` and only the REQs, journeys and FEATs the NEED touches; look in `docs/spec/needs/` for a NEED with the same request. Classify, first match wins:

| Type | Rule | Route |
|---|---|---|
| fix | a REQ, journey or decision already states the right behavior and the code does not | `routed`: a fix task row cites that artifact and the origin |
| content | only data changes, no rule | `routed`: the project's data-change flow |
| decision | a choice with nothing to deliver | `refine` to a decision record only |
| improvement | changes behavior an existing REQ or journey describes | `refine`: the REQ or journey changes |
| new | no REQ or journey covers it | `refine` |
| platform | process, tooling, CI or the kit | `refine` in the project's platform track |

- A problem with no artifact stating the right behavior is an improvement, never a fix. A duplicate closes `merged`, naming the NEED kept; a refused NEED closes `rejected` with its reason.
- Complete Problem / value and the Triage block: type and why, existing artifacts touched (with paths), Route, Size (`S`, `M` or `L`, no duration without a measured run), Priority (`now`, `next` or `later`; `later` closes `parked`, which returns to `triaged` when taken up).
- Finding facts is the agent's job. Open with a verdict and its evidence, then ask one question at a time with two to four options and a recommendation.
- Product confirms a `new`, `improvement`, `platform` or `decision` NEED, a `content` value, a rejection and a park (`Confirmed by: <name>, YYYY-MM-DD`). The agent routes a `fix` that cites the violated artifact's path and a duplicate that names the NEED kept, and records `Confirmed by: agent (fix|duplicate), product reviews later`.
- Set the status and add `YYYY-MM-DD specify: <type>, <route>, <priority>` to History. A routed NEED names the fix row or data change that took it.

## 2. Describe (route `refine`, when the NEED is taken up)

With product, fill in plain language:

- Desired outcome: what the actor can do or see when this is done, and the sign that it worked.
- Situations: who, when, expects; at least one that goes right and one that goes wrong. They are the input of `sdd-clarify`, so each names one case, not a solution.
- Scope, Out of scope (and where each excluded part goes), Constraints (deadline, budget, licence, platform, must-not).
- Evidence: an approved mock for a visual change, an `sdd-spike` report for a feel question (motion, camera, feedback, UI); stress-test a vague idea with `/grilling` first.

Set `status: specified` and add `YYYY-MM-DD specify: described` to History. More than five open questions mean the NEED holds several needs: split it (`parent`) before `specified`.

## 3. Validate

Run the project spec validator (`python3 .github/spec-lint/check_spec.py docs/spec .github/spec-lint/schemas`; in this kit, `platforms/tools/check.sh --spec docs/spec`) and paste its literal output.

## Rules

- No REQ, FEAT, decision, debt or task row; no technical choice (framework, table, message, algorithm).
- Links are written only in the NEED.

Done when: a decided NEED names type, route, size, priority and who confirmed, or says where it went or why it stopped; a described NEED has its outcome, Situations (right and wrong), scope and constraints, and validates as `specified`.
