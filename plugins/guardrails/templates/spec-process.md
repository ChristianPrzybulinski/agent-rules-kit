---
id: PROC-000
title: "[Process title: <actor or system> <does what>, one reusable flow]"
status: proposed
owner: "[product, or the team that runs a tech process]"
kind: product
created: "YYYY-MM-DD"
updated: "YYYY-MM-DD"
---

# PROC-000 — [Title]

<!-- kind: product (a mechanic or a business flow, seen by a user or not) or tech (a runbook, a scheduled routine
     such as keeping dependencies free of known vulnerabilities). One process may hold the steps of N FEATs: each FEAT
     is one use case, a slice of its steps. -->

## Trigger

- [FACT] [what starts it: an actor's action, an event, a schedule and who runs it, or a release step]

## Actors

- [FACT] [who or what takes part: user roles, the server, a scheduled job, an operator]

## Preconditions

- [FACT] [what must already hold: an earlier process's postconditions, services running, data in place]

## States

| State | Entry | Duration | Unit | Experience | Exit |
|---|---|---|---|---|---|
| [state] | [what enters it] | [n, or until <event>] | [frames, ticks, turns or seconds] | [what the actor sees, hears or gets] | [what leaves it, to which state] |

## Steps

| Step | Action → result | Rules | Implemented by | Proven by |
|---|---|---|---|---|
| S1 | [actor or system does … → result …] | REQ-F-nnn | — | — |
| S2 | [… → …] | REQ-F-nnn · REQ-NF-nnn | FEAT-nnn Tn | `clone-name/tests/**` · FEAT-nnn Tn · manual: [check] |

## Alternative paths

| Step | At | Action → result | Rules | Implemented by | Proven by |
|---|---|---|---|---|---|
| A1 | S1 | [failure, decision branch or variant → result] | REQ-F-nnn | — | — |

## Postconditions

- [FACT] [what holds when the main path ends: state saved, message sent, output (a fix NEED, a DEBT, a decision)]

## Out of this process

- [FACT] [adjacent flow and where it is covered: another process, a journey, or never]

## History

<!-- kind: tech: one `- YYYY-MM-DD: run: <result>` line per run; `spec_trace.py governance` shows the latest. -->
- YYYY-MM-DD: created.

<!-- Notes the checker (spec_trace.py) enforces:

  - Step ids: S<n> main path (in order), A<n> alternative (its `At` names the main step it diverts from), P<n>
    prerequisite (contracts, assets, tooling no actor sees). A first header cell `Step` marks a step table.
  - `Rules` cites REQ ids only, never rule values or free text: the rule text stays in its REQ.
  - `Implemented by` cites `FEAT-nnn Tn` task rows only, as they exist on main; rows of several FEATs may serve one
    process. In a `kind: tech` process, a main or alternative step a person runs, with no FEAT behind it, holds `—`
    for good when its `Proven by` is a `manual: <check>` alone.
  - A main or alternative step may hold a literal `—` in `Implemented by` and `Proven by` while an open NEED lists
    this process in `processes`, and its listed FEATs have not yet all delivered every REQ it lists.
  - `Proven by` holds `FEAT-nnn Tn` test tasks, backticked paths rooted at a clone name and an optional trailing
    `manual: <check>`.
  - A journey step cites this process as `PROC-000` (every step) or `PROC-000 S<a>–S<b>` (those main steps and the
    alternatives at them) and holds `—` in its own Rules, Implemented by and Proven by; the matrix expands it. A
    process step never cites another process.
  - The traceability matrix is generated (Processes, Rules → processes → tests, Tasks → processes), never edited by
    hand.
-->
