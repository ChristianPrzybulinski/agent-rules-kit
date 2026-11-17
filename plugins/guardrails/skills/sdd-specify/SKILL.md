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

Resolve the project profile first (`../session/references/project-profile.md`): `spec_root` (every `docs/spec` here) and `sdd`. With `sdd.needs: false` (`../sdd-constitution/references/sdd-parameters.md`) there is no NEED file: decide and describe in the conversation with the same rules, and `sdd-plan` writes the outcome (the Request quote, the Triage block with `Confirmed by`, the desired outcome, the Situations, scope and constraints) into the FEAT's Problem section; a `fix` or `content` request goes straight to its route, and a refused one ends in the conversation.

## 1. Decide (after intake, now or later; a recorded NEED may wait)

Read `docs/spec/spec.md` and only the REQs, journeys, processes and FEATs the NEED touches; look in `docs/spec/needs/` for a NEED with the same request. Classify, first match wins:

| Type | Rule | Route |
|---|---|---|
| fix | a REQ, journey, process or decision already states the right behavior and the code does not (a process states it in its steps, state exits and branches) | `routed`: a fix task row cites that artifact and the origin |
| content | only data changes, no rule | `routed`: the project's data-change flow |
| decision | a choice with nothing to deliver | `refine` to a decision record only |
| improvement | changes behavior an existing REQ, journey or process describes | `refine`: the REQ, journey or process changes |
| new | no REQ, journey or process covers it | `refine` |
| platform | process, tooling, CI or the kit | `refine` in the project's platform track |

- A problem with no artifact stating the right behavior is an improvement, never a fix. A duplicate closes `merged`, naming the NEED kept; a refused NEED closes `rejected` with its reason.
- Pillars and Out of scope (on when `spec.md` has them, as journeys are on when the folder exists): a NEED that hits an `Out of scope (explicit)` line closes `rejected` (the line says never) or `parked` (it names a later milestone), and its Route cites that line (`spec.md:<line>` and its text). While `spec.md` has `## Pillars`, a `new`, `improvement`, `content` or `decision` NEED names the pillar it serves (`Pillar: P<n>` and how); one that serves none closes `rejected` or `parked` the same way, citing the Pillars table. A `fix` (it restores stated behavior) and a `platform` NEED write `Pillar: —`. `sdd-check` C13 flags a miss.
- Complete Problem / value and the Triage block: type and why, existing artifacts touched (with paths), Pillar, Route, Size (`S`, `M` or `L`, no duration without a measured run), Priority (`now`, `next` or `later`; `later` closes `parked`, which returns to `triaged` when taken up).
- Finding facts is the agent's job. Open with a verdict and its evidence, then ask one question at a time with two to four options and a recommendation.
- Product confirms a `new`, `improvement`, `platform` or `decision` NEED, a `content` value, a rejection and a park (`Confirmed by: <name>, YYYY-MM-DD`). The agent routes a `fix` that cites the violated artifact's path and a duplicate that names the NEED kept, and records `Confirmed by: agent (fix|duplicate), product reviews later`.
- Set the status and add `YYYY-MM-DD specify: <type>, <route>, <priority>` to History. A routed NEED names the fix row or data change that took it.

## 2. Describe (route `refine`, when the NEED is taken up)

With product, fill in plain language:

- Desired outcome: what the actor can do or see when this is done, and the sign that it worked; its `Experience` line holds the feeling it should give, in the actor's own words (the register: `../sdd-constitution/references/sdd-process.md` § Register).
- Situations: who, when, expects; at least one that goes right and one that goes wrong. They are the input of `sdd-clarify`, so each names one case, not a solution.
- Scope, Out of scope (and where each excluded part goes), Constraints (deadline, budget, licence, platform, must-not).
- Evidence: an approved mock for a visual change, an `sdd-spike` report for a feel question (motion, camera, feedback, UI).

Set `status: specified` and add `YYYY-MM-DD specify: described` to History. More than five open questions mean the NEED holds several needs: split it (`parent`) before `specified`.

## 3. Validate

Run the spec validator (`CHECK_SPEC`; in this kit, `platforms/tools/check.sh --spec docs/spec`) and paste its literal output.

## Rules

- No REQ, FEAT, decision, debt or task row; no technical choice (framework, table, message, algorithm).
- Links are written only in the NEED.

Done when: a decided NEED names type, pillar (or `—`), route, size, priority and who confirmed, or says where it went or why it stopped; a described NEED has its outcome, Situations (right and wrong), scope and constraints, and validates as `specified`.
