---
description: "Processes PROC-nnn: states, steps, decisions and feedback that journeys cite; written in clarify, checked by sdd-check C12. Load when a flow changes."
kind: detail
---

# Processes

A process (`PROC-nnn`) holds one reusable functional flow: a mechanic, a business flow, or a flow no user sees (a scheduled job, a server count). Journeys stay the end-to-end paths and cite it (`journeys.md`); the rule text stays in the REQs it cites. Template: `../../../templates/spec-process.md`; file `docs/spec/processes/PROC-nnn.md`; `check_spec.py` validates it and `spec_trace.py` checks and expands its steps (KIT-090).

## When

- `sdd-clarify` writes a process when a NEED's Situations add or change a flow that two flows share, that one journey would copy from another ("as in J-nn"), that no user sees, or that is one mechanic with states; else the steps stay in the journey. A product NEED changing an existing process amends it.
- `kind: product` for a mechanic or a business flow; `kind: tech` for a runbook or a scheduled routine (an operator's flow, owned by the team that runs it).
- The NEED lists each process it adds or changes in `processes`; while that NEED is open, the process's `—` steps wait (`journeys.md` § Write).

## Write

- Trigger, Actors, Preconditions and Postconditions: one fact each; a precondition may be another process's postcondition.
- States: one row per state the actor experiences. Entry names the step or state that enters it; Exit names every way out and the state (or `end`) it goes to. Duration is a number or `until <event>`, with its unit (frames, ticks, turns or seconds); a duration the actor feels and product may retune is a value of the REQ the step cites, whose `Tunable` cell gives range, unit and exposure (`req-scope.md` § 1), never a second number here.
- Steps: the journey's columns and ids (`S<n>`, `A<n>` with `At`, `P<n>`); Rules hold REQ ids only, or `—`; Implemented by and Proven by hold `—` until `sdd-tasks` fills them; a `kind: tech` step a person runs, with no FEAT behind it, keeps `—` in Implemented by with a `manual: <check>` alone in Proven by.
- Decisions: a step whose result depends on a condition is a decision point. The main path takes one branch; every other branch is an `A<n>` row at that step with its own result, and each failure the Situations name (invalid input, timeout, refusal) is a branch.
- Feedback: an action the actor takes names, in its result cell, what the actor gets back (visual, sound or message) and when (at once, after the state ends, on failure): a game's hit flash, a business form's loading and error states.
- Register: a product process reads in PO language, as a journey does (actor, action, visible result, glossary terms, states, REQ ids; no endpoint, table, class, file path or engine call: "the player dashes 120 px; touching a wall stops the dash"). A tech process may name tools, commands, hosts and schedules.
- Out of this process: each adjacent flow and where it lives.

## Soundness (what `sdd-check` C12 reads)

1. Every state is entered: the first from the Trigger, each other from a step or another state's Exit.
2. Every state exits, to another state or to `end`; a state with no way out is a dead end unless the Postconditions name it as final.
3. Every decision point has a row for each branch: the main step plus one `A<n>` per other outcome, with no outcome left as "otherwise".
4. Every step's rule is a REQ id; a rule written as prose in an action or result cell becomes a REQ (`req-scope.md`) in the same change.

## Sign and change

- Product signs a product process (`status: approved`) when its NEED is refined; the owner team signs a tech one. A retired flow is `retired`, never deleted.
- Regenerate the matrix after a process or journey changes: `TRACE generate <spec_root>` (`../../session/references/project-profile.md` § 3), then `check`.
- A FEAT is one use case, a slice of a process's steps; one process may hold the steps of several FEATs. `sdd-plan` § Design cites each state the FEAT implements.
