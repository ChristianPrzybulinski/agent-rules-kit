---
name: sdd-plan
description: "SDD step 4 — create the FEAT for a refined NEED: technical plan and decisions. Use when a NEED is refined. Not for task breakdown (skill sdd-tasks)."
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

The technical refinement: creates the FEAT, one delivery that implements approved REQs, and plans it. Process: `../sdd-constitution/references/sdd-process.md`. Template: `../../templates/spec-feature.md`.

## 1. Confirm readiness

Require a NEED with `status: refined` whose REQs are `approved`. Read the actual modules/files plus repository rules; do not infer structure from the desired design.

## 2. Create the FEAT

- Take the next unused `FEAT-nnn` (or the session's reserved block) and create it from the template with `status: proposed`.
- `requirements`: the REQs this delivery implements, new or amended; add the FEAT to each of those REQs' `features` (both sides list the link). REQs left to another delivery stay in Out of scope.
- Problem / value: one line and the NEED id; the NEED keeps the full problem, Situations and scope. Scope lists the REQs delivered.
- Acceptance criteria are technical (contract, unit, integration, e2e); each cites in `Proves` the REQ ids it proves, and every REQ in Scope is proved by at least one criterion. The REQs' examples and counterexamples are the functional criteria; do not restate them.
- Add the FEAT to the NEED's `features` and a History line.

## 3. Write the FEAT Plan

Cover:

- domain aggregates/value objects/events and protected invariants;
- client, server, protocol and adapter boundaries;
- changed messages/endpoints with compatibility and protocol-version effect;
- tables/columns, `V<n>__slug.sql`, indexes, transaction and idempotency;
- feature flag name, default and off behavior, or why none is needed;
- each acceptance criterion's test type/location;
- logs/metrics, hypotheses with validation (at most three load-bearing risks, each `Fails if <condition>` with its cheapest test; one that needs code becomes an `sdd-spike`), each external API with its exact signature and the source read this session, dependencies and blockers.

## 4. Record decisions

A technical choice with a rejected reasonable alternative gets a decision record (`DEC-nnn`, or the prefix of its kind when `docs/spec/spec.md` declares `decision_kinds`) with `status: proposed`. A product choice is not made here: it returns to `sdd-clarify`. Do not hide a kit-rule exception in prose—record a blocker or explicit decision.

## 5. Check restraint and consistency

Do not add queue/cache/service/layer without demonstrated need. Ensure every criterion has a planned proof, run `sdd-check FEAT-nnn` (full scope: the functional items again plus the technical ones) with no critical/high findings, then set `status: planned` and update History.

Done when: the FEAT lists the REQs it delivers on both sides, every REQ in Scope is proved by a criterion, the Plan names real files/boundaries, decisions have a record or justification, and the full check is unblocked.
