---
description: Wave assignment, complexity tiers, the model directive and the longest-chain limits for task rows. Load when filling the cut fields.
kind: detail
---

# Task rows — waves and model tiers

## Waves

- Contracts, schemas and DECs go to wave 0; wave 0 runs sequentially.
- A consumer depends on the merged contract row, never on the producer's implementation row: producer and consumer then share a wave instead of chaining.
- Two tasks share a wave only when neither reads the other's output and their file sets are disjoint — or, once a `git merge-tree` replay of past work shows the shared files merge cleanly (skill `sdd-implement`, its reference `measure-conflicts.md`), when they share only such files. A semantic hotspot (migration number, protocol version, error-code allocation) still separates them.
- Wave numbers are FEAT-local; a cross-FEAT dependency points to a task cut earlier (an earlier wave in the published cut order).
- Items are cut in wave order; an executor runs one wave at a time and starts the next only when the `Depends on` chain is merged.

## Complexity → model tier

| Complexity | `Model` cell | Meaning |
|---|---|---|
| Low | `small` | small/fast tier |
| Med | `mid` | mid tier |
| High | `top` | top tier at maximum effort |

- A row is High only when it needs the stronger model: a design judgment the Plan could not settle, concurrency, security or a subtle invariant. Size alone is never a reason: a large row is split.
- The row value is `Med`, never `Medium`.
- A project maps tiers to vendor model names in its own AGENTS.md or ARCHITECT file; the kit never names a vendor model.
- Effort is set once per tier in the executor's model picker; the task row does not repeat it.
- A human executor reads the tier as a hint; `Complexity` still sets the review depth.

## The longest chain

- The longest chain of own rows is at most `max_chain` (`check_spec.py` fails above it).
- A row on the longest chain is Med at most, so the critical path never waits on the top tier.
- A High row is split along its Plan steps (one row per step of the Plan section it implements), each step at Med or Low where it can be, before it is allowed on the chain.

## Worked example

A FEAT cut across three waves:

| Wave | Row | Files | Why this wave |
|---|---|---|---|
| 0 | T1 Define contract | `protocol/... , tests/...` | contracts are sequential and first |
| 1 | T2 Server handler, T3 Client mapper | `server/...` / `client/...` | disjoint file sets; both read only the merged contract |
| 2 | T4 Integration | `tests/e2e/...` | reads the output of T2 and T3 |

`Depends on`: T2 and T3 → `T1` (the contract, not each other); T4 → `T2, T3`. Longest chain: T1 → T2 → T4, three rows, all Med or Low.
