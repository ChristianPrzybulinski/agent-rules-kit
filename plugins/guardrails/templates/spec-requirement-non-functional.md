---
id: REQ-NF-000
title: "[Quality attribute in 1 measurable sentence]"
type: non-functional
category: performance
priority: should
metric: "[what to measure, unit]"
target: "[value or HYPOTHESIS]"
measurement: "[how/where to measure]"
features: []
created: "YYYY-MM-DD"
---

# REQ-NF-000 — [Title]

## Statement

[E.g.: The server must process a client action in ≤ 100 ms (p95) with 50 simultaneous sessions.]

## Metric and target

| Metric | Target | Target state | How to measure |
|---|---|---|---|
| [p95 action latency] | [100 ms] | `[HYPOTHESIS]` until a load test | [tool, scenario, environment] |

A target without a planned measurement is not a requirement — it is a wish. Mark `[HYPOTHESIS]` and say when it will be measured.

## Rationale

[Why this value. Source if any.]

## Affected features

- `FEAT-000`
