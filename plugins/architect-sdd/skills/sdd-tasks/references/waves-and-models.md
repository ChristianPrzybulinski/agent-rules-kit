---
description: Wave assignment, complexity tiers and the model directive for task rows. Load when filling the cut fields.
kind: detail
---

# Task rows — waves and model tiers

## Waves

- Contracts, schemas and DECs go to wave 0; wave 0 runs sequentially.
- Two tasks share a wave only when their file sets are disjoint and neither reads the other's output.
- Wave numbers are FEAT-local; a cross-FEAT dependency points to a task cut earlier (an earlier wave in the published cut order).
- Issues are cut in wave order; an executor runs one wave at a time and starts the next only when the `Depends on` chain is merged.

## Complexity → model tier

| Complexity | `Model` cell | Meaning |
|---|---|---|
| Low | `small` | small/fast tier |
| Med | `mid` | mid tier |
| High | `top` | top tier at maximum effort |

- The row value is `Med`, never `Medium`.
- A project maps tiers to vendor model names in its own AGENTS.md or ARCHITECT file; the kit never names a vendor model.
- Effort is set once per tier in the executor's model picker; the task row does not repeat it.
- A human executor reads the tier as a hint; `Complexity` still sets the review depth.

## Worked example

A FEAT cut across three waves:

| Wave | Row | Files | Why this wave |
|---|---|---|---|
| 0 | T-01 Define contract | `protocol/... , tests/...` | contracts are sequential and first |
| 1 | T-02 Server handler, T-03 Client mapper | `server/...` / `client/...` | disjoint file sets, neither reads the other's output |
| 2 | T-04 Integration | `tests/e2e/...` | reads the output of T-02 and T-03 |

`Depends on`: T-02 and T-03 → `FEAT-nnn T1`; T-04 → `FEAT-nnn T2, T3`.
