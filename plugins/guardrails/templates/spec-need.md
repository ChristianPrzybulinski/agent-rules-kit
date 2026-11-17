---
id: NEED-000
title: "[The need in one business sentence: Users can recover a forgotten password]"
type: new
status: proposed
origin: "[owner | user report <ref> | team | audit <ref>]"
parent: null
requirements: []
journeys: []
decisions: []
debts: []
features: []
created: "YYYY-MM-DD"
updated: "YYYY-MM-DD"
---
<!-- type: new | improvement | fix | content | platform | decision. Provisional at intake, confirmed by sdd-specify.
     status: proposed (sdd-intake) → triaged (sdd-specify, decide) → specified (sdd-specify, describe) → refined
     (sdd-clarify, after a clean functional sdd-check) → delivered (with its last FEAT, by sdd-release or sdd-review; a decision
     NEED with no FEAT, by sdd-clarify when it approves the decision; check_spec.py refuses it before), or closed
     rejected | merged | routed | parked; a parked NEED returns to triaged when taken up.
     requirements, journeys and decisions are filled by sdd-clarify; features by sdd-plan. Links are written here only:
     REQ, FEAT, decision and debt files never list NEEDs in their link fields; they cite it only as provenance.
     Register (skills/sdd-constitution/references/sdd-process.md, Register): the user's own language, simple, the idea;
     no solution, framework, table, endpoint, class or file path. -->

# NEED-000 — [Title]

## Request
<!-- sdd-intake. The words of whoever asked, verbatim and in their language, with date and channel. Never edited; a
     later restatement is a new dated quote below. -->

> "[verbatim]" — [who], YYYY-MM-DD, [channel]

## Problem / value
<!-- sdd-intake: one line. sdd-specify (decide): complete. For whom, what problem, why now. No solution. -->

## Desired outcome
<!-- sdd-specify (describe). What the actor can do or see when this is done, and the sign that it worked. Experience:
     the feeling it should give, in the actor's (the player's, the user's) own words. -->

Experience: [the feeling, in the actor's words]

## Situations
<!-- sdd-specify (describe). Plain-language cases, at least one that goes right and one that goes wrong. sdd-clarify
     turns each into REQs, a journey step or a cut. -->

| # | Who | When | Expects |
|---|---|---|---|
| S1 | [actor] | [situation] | [visible result] |
| S2 | [actor] | [something goes wrong] | [visible result] |

## Scope
<!-- sdd-specify (describe). -->

- [included]

## Out of scope
<!-- sdd-specify (describe). -->

- [excluded, and where it goes: another NEED, later, never]

## Constraints
<!-- sdd-specify (describe). -->

- [deadline, budget, licence, platform, must-not]

## Evidence
<!-- Any step. [FACT] items with their source: report, screenshot, reference, measurement, approved mock, spike
     report. Bulky data goes in NEED-000-data/ beside this file. -->

## Triage
<!-- sdd-specify (decide). -->

- Type: [type], because [one line]
- Existing artifacts touched: [REQ-F-nnn, J-NN, FEAT-nnn with path] or —
- Pillar: [P<n> from spec.md Pillars, and how it serves it | — (a fix or platform NEED, or spec.md has no Pillars)]
- Route: [refine | fix row citing REQ-x | data PR | decision only | split into NEED-a, NEED-b | merge into NEED-x |
  reject: reason or the spec.md Out of scope line | park: the Out of scope line, when one applies]
- Size: [S | M | L] (no duration without a measured run)
- Priority: [now | next | later] (later = parked)
- Confirmed by: [product name], YYYY-MM-DD | agent (fix|duplicate), product reviews later

## Open questions
<!-- Any step; sdd-clarify closes the last one before refined. -->

- [NEEDS CLARIFICATION: ...]

## Refinement
<!-- sdd-clarify. One row per Situation: the REQ written, reused or amended, the journey step, the decision, or the cut. -->

| Situation | Became | Why |
|---|---|---|
| S1 | [REQ-F-nnn new / REQ-F-nnn amended / J-NN S<n> / decision id / cut: where it went] | [one line] |

## History
<!-- Every step. sdd-intake writes the first line; each later step appends `YYYY-MM-DD <step>: <what>` for its status
     move, answer or check (specify, clarify, plan, delivery). -->

- YYYY-MM-DD intake: created from [channel].
