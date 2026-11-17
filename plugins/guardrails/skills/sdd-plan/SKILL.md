---
name: sdd-plan
description: "SDD step 4 — one FEAT per delivery of a refined NEED: its Plan sections and decisions. Use when a NEED is refined. Not for task rows (skill sdd-tasks)."
argument-hint: "NEED-nnn [technical constraints]"
triggers:
  - user
disable-model-invocation: true
allowed-tools:
  - read
  - glob
  - grep
  - edit
  - exec
---

# SDD 4 — Plan

The technical refinement: cuts a refined NEED into deliveries, creates one FEAT per delivery and plans it. Process: `../sdd-constitution/references/sdd-process.md`. Template: `../../templates/spec-feature.md`. It reads the parameters `plan_sections` and `max_feat_tasks` from `check_spec.py --params` (`../sdd-constitution/references/sdd-parameters.md`), and `decision_folding` from the project profile (`python3 ~/.ai-kit/platforms/tools/profile.py resolve --section sdd`).

## 1. Confirm readiness

Require a NEED with `status: refined` whose REQs are `approved`; with `sdd.needs: false` (no NEED file), the request `sdd-specify` decided and the approved REQs `sdd-clarify` wrote, which land in this change, and Problem / value holds what the NEED would: the Request quote, the Triage block, the desired outcome, the Situations, scope and constraints. Read the actual modules/files plus repository rules; do not infer structure from the desired design.

## 2. Cut the NEED into deliveries

- One FEAT per delivery: a set of whole REQs that ships and is proved on its own. Never a bucket FEAT that collects unrelated work or keeps taking rows; later work is a new NEED.
- A NEED of type `platform` (tooling, CI, process) gets its own FEAT, never rows inside a product FEAT.
- Estimate each delivery's rows (one per verifiable outcome, `sdd-tasks` § 2). Above `max_feat_tasks`, split the NEED into several FEATs ordered by `depends_on`; `check_spec.py` warns when a task table outgrows it.

## 3. Create each FEAT

- Take the next unused `FEAT-nnn` (or the session's reserved block) and create it from the template with `status: proposed`.
- `requirements`: the REQs this delivery implements, new or amended; add the FEAT to each of those REQs' `features` (both sides list the link). REQs left to another delivery stay in Out of scope.
- Problem / value: one line and the NEED id; the NEED keeps the full problem, Situations and scope. Scope lists the REQs delivered.
- Acceptance criteria are technical (contract, unit, integration, e2e); each cites in `Proves` the REQ ids it proves, and every REQ in Scope is proved by at least one criterion. The REQs' examples and counterexamples are the functional criteria; do not restate them.
- Add the FEAT to the NEED's `features` and a History line.

## 4. Write the Plan sections

`## Plan` holds one `### <section>` per name in `plan_sections`, in this order: Design, Contract, Data, UI, Flag, Tests, Observability, Risks, Dependencies (`Risks` and `Tests` always). Each holds its content or one line `— <why it does not apply>`. What each section holds: `references/plan-sections.md`. The standards each section applies:

| Section | Reference |
|---|---|
| Design | `references/architecture.md` (blocks: `references/pattern-catalog.md`); a trust boundary `references/security-design.md`; a service `references/twelve-factor.md`; a Godot client `references/godot/README.md` |
| Contract | `references/contract.md` |
| Data | `references/data.md` (versions `references/postgres-18.md`, `references/redis-7.md`) |
| Tests | skill `sdd-implement`, references `tdd.md` and `test-gates.md` |

- The Plan is the design: every choice the rows need is made here, so a task cell points to `Plan § <section>` and never restates it.
- Contract: every changed message, endpoint, schema or table another FEAT reads passes the four checks of `references/contract.md`.
- Name real rooted files and the architecture areas of `docs/spec/spec.md` § Architecture each change lands in.

## 5. Record decisions

A technical choice with a rejected reasonable alternative that outlives the FEAT (other FEATs or later work rely on it) gets a decision record (`DEC-nnn`, or the prefix of its kind when `docs/spec/spec.md` declares `decision_kinds`) with `status: proposed`. A choice that matters only inside this delivery stays in its Plan section, the rejected alternative in one line. A product choice is not made here: it returns to `sdd-clarify`. Several open choices form a tree, as the questions of `sdd-clarify` § 2 do: settle only from its frontier, the choice the others depend on first, one choice per question when it needs the owner, and never one whose answer hinges on a choice still open. Do not hide a kit-rule exception in prose—record a blocker or explicit decision.

Fold settled decisions (the `decision_folding.marker` of the project profile, default `→ folded into`): a `[DECISION]` line settled in the FEAT's `## Open questions` is not edited or deleted. The next spec PR that touches the FEAT (a Plan amendment, the `sdd-tasks` rows, a resync) writes the decision where it belongs, as a Scope bullet, an acceptance criterion with its Given/When/Then, or the REQ (a REQ change goes through `sdd-clarify`), and appends the marker and the target to the line: `→ folded into CA-3`. Open questions lists the unfolded lines first. Task `Status` needs no folding: it is derived from the items (`sdd-tasks` § 5).

## 6. Check restraint and consistency

Do not add queue/cache/service/layer without demonstrated need. Ensure every criterion has a planned proof in Tests, run `sdd-check FEAT-nnn` (full scope: the functional items again plus the technical ones; C8's task half waits for `sdd-tasks`) with no critical/high findings, then set `status: planned` and update History.

Done when: each FEAT is one delivery within `max_feat_tasks`, lists the REQs it delivers on both sides, proves every REQ in Scope by a criterion, holds every `plan_sections` section (content or `— <why>`) naming real files, passes the contract checks, gives each lasting choice a decision record and the full check is unblocked.
