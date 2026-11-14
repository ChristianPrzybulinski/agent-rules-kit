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
<!-- type: new | improvement | fix | content | platform | decision. Provisional at capture, confirmed at triage.
     status: proposed → triaged → refined → delivered, or rejected | merged | routed | parked.
     delivered follows the linked FEATs (check_spec.py refuses it while one is not delivered); every other status is
     set by its step. Links are written here only: REQ, FEAT, decision and debt files never list NEEDs. -->

# NEED-000 — [Title]

## Request
<!-- Capture. The words of whoever asked, verbatim and in their language, with date and channel. Never edited; a later
     restatement is a new dated quote below. -->

> "[verbatim]" — [who], YYYY-MM-DD, [channel]

## Problem / value
<!-- Capture: one line. Triage: complete. For whom, what problem, why now. No solution. -->

## Desired outcome
<!-- Refinement start (sdd-specify), not triage. What the actor can do or see when this is done, and the sign that
     it worked. -->

## Situations
<!-- Refinement start (sdd-specify), not triage. Plain-language cases, at least one that goes right and one that goes
     wrong. Each becomes one or more REQs. -->

| # | Who | When | Expects |
|---|---|---|---|
| S1 | [actor] | [situation] | [visible result] |
| S2 | [actor] | [something goes wrong] | [visible result] |

## Scope
<!-- Refinement start (sdd-specify), not triage. -->

- [included]

## Out of scope
<!-- Refinement start (sdd-specify), not triage. -->

- [excluded, and where it goes: another NEED, later, never]

## Constraints
<!-- Refinement start (sdd-specify), not triage. -->

- [deadline, budget, licence, platform, must-not]

## Evidence
<!-- Any step. [FACT] items with their source: report, screenshot, reference, measurement. Bulky data goes in
     NEED-000-data/ beside this file. -->

## Triage
<!-- sdd-triage. -->

- Type: [type], because [one line]
- Existing artifacts touched: [REQ-F-nnn, J-NN, FEAT-nnn with path] or —
- Route: [refine | fix row citing REQ-x | data PR | decision only | split into NEED-a, NEED-b | merge into NEED-x |
  reject: reason | park]
- Size: [S | M | L] (no duration without a measured run)
- Priority: [now | next | later] (later = parked)
- Confirmed by: [product name], YYYY-MM-DD | agent (fix|duplicate), product reviews later

## Open questions

- [NEEDS CLARIFICATION: ...]

## Refinement
<!-- Filled by functional refinement: what each Situation became. -->

| Situation | Became | Why |
|---|---|---|

## History

- YYYY-MM-DD capture: created from [channel].
