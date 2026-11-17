---
description: Journeys and processes — J-NN steps cite REQ ids, processes, tasks and tests; written in clarify, checked by sdd-check. Load when a NEED changes a user flow.
kind: detail
---

# Journeys and processes

Only for a project that keeps `docs/spec/journeys/` (`sdd.journeys`). A journey is one user-visible flow of two or more screens or interactions, written as an ordered set of steps; it cites rule ids, processes, task rows and tests, never rule values. A process (`PROC-nnn`) holds one reusable functional flow, such as a mechanic or a flow no user sees, and a journey step may cite it whole (`PROC-nnn`) or a range of its steps (`PROC-nnn S<a>–S<b>`) instead of copying them. Template: `../../../templates/spec-journey.md`.

When to write a process, its states, decisions and feedback, and the soundness `sdd-check` C12 reads: `processes.md`; its steps follow the rules below. A step reused from another flow cites its process, never "as in J-nn" in place of its own links.

## When

- `sdd-clarify` updates a journey when a NEED's Situations add, change, reorder or remove a step of a flow, and creates `docs/spec/journeys/J-NN.md` for a new flow. A flow documented without a product change enters as its own NEED.
- A flow is planned together with its journey: the rules the journey uses are REQs before `sdd-plan` cuts the FEAT, never FEAT-local text; a step whose rule has none gets one through `req-scope.md` in the same change.
- `sdd-check` runs the matrix check below in its functional and full scopes; a failure blocks `refined` or `planned`.

## Write

- From the template: `status: proposed`, `owner`, `created`, `updated`.
- Step tables (first header cell `Step`): `S<n>` main path in order, `A<n>` alternative with `At` naming its main step, `P<n>` prerequisite (contracts, assets, tooling no user sees), which always cites its task, so `sdd-tasks` adds it with the row.
- `Rules` holds REQ ids only, or `—`. The rules already are REQs.
- `Implemented by` holds `FEAT-nnn Tn` rows as they are on main; `Proven by` holds test tasks, backticked paths rooted at a clone name, and an optional trailing `manual: <check>`. A main or alternative step written here holds a literal `—` in both, and `sdd-tasks` fills both when it cuts the rows (`Proven by` with test task rows until the test file exists). `spec_trace.py` accepts the `—` while a NEED that lists the journey in `journeys` is open (not `delivered`, `rejected`, `merged`, `routed` or `parked`, and its FEATs have not yet all delivered every REQ it lists); once none is, both are required, and a project without `docs/spec/needs/` never waits. An empty cell fails.
- A step that cites a process holds `—` in Rules, Implemented by and Proven by: the process's steps carry them, `spec_trace.py` expands `PROC-nnn` to every step and `PROC-nnn S<a>–S<b>` to those main steps and the alternatives at them. A prerequisite never cites a process. A process step's `—` waits while an open NEED lists the process in `processes`.

## Link once, generate

- Journey → rule, process, task and test links are written only in the journey (or the process); no FEAT, REQ or task lists journeys, and the NEED's `journeys` field only records which journeys it changed (while the NEED is open, their `—` steps wait).
- Regenerate the matrix with the kit's validator (`generate`, then `check` must pass) after a journey or a FEAT↔REQ link changes: `TRACE generate <spec_root>` (`../../session/references/project-profile.md` § 3); never edit `traceability.md` by hand.
- Product signs the journey: `status: approved`, when its NEED is refined; a retired flow is `retired`, never deleted.

## Check a change

- The review of a PR that changes a REQ, a FEAT or a journey reads `spec_trace.py impact docs/spec <base> <head>` (the journey steps and tests the diff touches) and checks each listed step and its tests.
- The journey steps a code PR's task serves are in `traceability.md` § Tasks → journeys, its process steps in § Tasks → processes.
