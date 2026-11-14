---
name: sdd-intake
description: "SDD entry — record an idea, need, improvement or problem as a NEED-nnn and route it. Use when a request arrives. Not for writing REQs (skill sdd-specify)."
argument-hint: "<request in natural language> | NEED-nnn"
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

# SDD entry — Intake

Every request enters here: it becomes a `NEED-nnn` under `docs/spec/needs/`, or is routed when it needs no refinement. This skill captures and triages; it writes no REQ, FEAT, decision, debt, task row or code. Process: `../sdd-constitution/references/sdd-process.md`. Template: `../../templates/spec-need.md`.

## 1. Capture

- Take the next unused `NEED-nnn`, or the first unused id of the block the session prompt reserves, and create `docs/spec/needs/NEED-nnn-slug.md` from the template, keeping every section.
- At capture fill only the title, a provisional `type`, `origin`, the Request quote (verbatim, in the asker's language, with date and channel) and one line of Problem / value; every other section holds `—`. Capture costs one file, so a request is recorded before anyone judges it.
- A request holding several needs becomes one NEED each; the first records the request and lists the others in Triage, and each of them sets `parent` to it.

## 2. Triage

Read `docs/spec/spec.md` and only the REQs, journeys and FEATs the request touches. Classify, first match wins:

| Type | Rule | Route |
|---|---|---|
| fix | a REQ, journey or decision already states the right behavior and the code does not | `routed`: a fix task row cites that artifact and the origin |
| content | only data changes, no rule | `routed`: the project's data-change flow |
| decision | a choice with nothing to deliver | `refine` to a decision record only |
| improvement | changes behavior an existing REQ or journey describes | `refine`: the REQ or journey changes |
| new | no REQ or journey covers it | `refine` |
| platform | process, tooling, CI or the kit | `refine` in the project's platform track |

- A problem with no artifact stating the right behavior is an improvement, never a fix.
- A duplicate closes `merged` (Route names the NEED kept); one accepted for later is `parked`; a refused one is `rejected` with its reason.
- Complete Problem / value, Desired outcome, Situations (at least one case that goes right and one that goes wrong), Scope, Out of scope, Constraints, Evidence and the Triage block.
- Finding facts is the agent's job; type, route, scope and priority are product's. Open with a verdict and its evidence, then ask one question at a time with two to four options and a recommendation. A vague idea is stress-tested with `/grilling`; a feel question (motion, camera, feedback, UI) gets an `sdd-spike`, whose report becomes Evidence.
- Set `status: triaged` only once product fills `Confirmed by`.

## 3. Hand off

- `refine` → `sdd-specify`, which starts from this NEED and writes its ids back into the NEED's frontmatter; a new or changed user-visible flow also goes to `sdd-journey`.
- `routed`, `merged`, `parked` and `rejected` keep the file; Route says where the work went or why it stopped.
- Every status change adds one History line: `YYYY-MM-DD <step>: <what changed>`.

## 4. Validate

Run the project spec validator (`python3 .github/spec-lint/check_spec.py docs/spec .github/spec-lint/schemas`; in this kit, `platforms/tools/check.sh --spec docs/spec`) and paste its literal output.

## Rules

- Never edit the Request quote's meaning, and never write a REQ, FEAT, decision, debt or task row in this step.
- Links are written only in the NEED; REQ, FEAT, decision and debt files never list NEEDs.
- No duration estimate without a measured run.

Done when: the NEED validates, its status matches the step it passed, and a routed or closed NEED names where the work went or why it stopped.
