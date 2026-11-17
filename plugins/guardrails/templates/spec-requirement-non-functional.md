---
id: REQ-NF-000
title: "[Quality attribute in 1 measurable sentence]"
type: non-functional
status: proposed
category: performance
priority: should
metric: "[what to measure, unit]"
target: "[value or HYPOTHESIS]"
measurement: "[how/where to measure]"
features: []
source: "[NEED-nnn S<n> | <decision id>]"
created: "YYYY-MM-DD"
---
<!-- Written by sdd-clarify; a measured quality (p95, %, MB, frames, uptime) or a property across many behaviors, never
     one scenario (that is a REQ-F). Scope rules: skills/sdd-clarify/references/req-scope.md.
     status: proposed → approved (product, when its NEED is refined) → retired. Absent means approved.
     features is filled by sdd-plan; until then the NEED that lists this REQ is its link.
     Register (skills/sdd-constitution/references/sdd-process.md, Register): PO, functional: the quality, its metric
     and target, never how the code reaches it. -->

# REQ-NF-000 — [Title]

## Statement

[E.g.: The server must process a client action in ≤ 100 ms (p95) with 50 simultaneous sessions.]

## Metric and target

| Metric | Target | Target state | How to measure |
|---|---|---|---|
| [p95 action latency] | [100 ms] | `[HYPOTHESIS]` until a load test | [tool, scenario, environment] |

A target without a planned measurement is not a requirement — it is a wish. Mark `[HYPOTHESIS]` and say when it will be measured.

## Rationale

[Why this value: the NEED Situation or constraint it comes from (NEED-nnn S<n>), and the source of the number if any.]

## Verification

- Counterexamples: [a measurement that would violate the target]

## Affected features

- `FEAT-000` <!-- sdd-plan -->

## History

- YYYY-MM-DD NEED-nnn: created — [why, one line].
