---
description: Journey layer — J-NN steps cite REQ ids, tasks and tests; written during clarify, checked by sdd-check. Load when a NEED changes a user-visible flow.
kind: detail
---

# Journeys

Only for a project that keeps `docs/spec/journeys/`. A journey is one user-visible flow of two or more screens or interactions; it orders the steps and cites rule ids, task rows and tests, never rule values. Template: `../../../templates/spec-journey.md`.

## When

- `sdd-clarify` updates a journey when a NEED's Situations add, change, reorder or remove a step of a flow, and creates `docs/spec/journeys/J-NN.md` for a new flow. A flow documented without a product change enters as its own NEED.
- `sdd-check` runs the matrix check below in its functional and full scopes; a failure blocks `refined` or `planned`.

## Write

- From the template: `status: proposed`, `owner`, `created`, `updated`.
- Step tables (first header cell `Step`): `S<n>` main path in order, `A<n>` alternative with `At` naming its main step, `P<n>` prerequisite (contracts, assets, tooling no user sees), which always cites its task, so `sdd-tasks` adds it with the row.
- `Rules` holds REQ ids only, or `—`. The rules already are REQs: a step whose rule has none gets one through `req-scope.md` in the same change.
- `Implemented by` holds `FEAT-nnn Tn` rows as they are on main; `Proven by` holds test tasks, backticked paths rooted at a clone name, and an optional trailing `manual: <check>`. A main or alternative step written here holds a literal `—` in both, and `sdd-tasks` fills both when it cuts the rows. `spec_trace.py` accepts the `—` while a NEED that lists the journey in `journeys` is open (not `delivered`, `rejected`, `merged`, `routed` or `parked`); once none is, both are required, and a project without `docs/spec/needs/` never waits. An empty cell fails.

## Link once, generate

- Journey → rule, task and test links are written only in the journey; no FEAT, REQ or task lists journeys, and the NEED's `journeys` field only records which journeys it changed (while the NEED is open, their `—` steps wait).
- Regenerate the matrix with the project's copy of the validator (`spec_trace.py generate`, then `check` must pass), e.g. `.github/spec-lint/spec_trace.py docs/spec`, synced by `platforms/tools/sync-project.sh`; never edit `traceability.md` by hand.
- Product signs the journey: `status: approved`, when its NEED is refined; a retired flow is `retired`, never deleted.
