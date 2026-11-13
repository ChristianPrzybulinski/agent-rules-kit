---
name: sdd-plan
description: SDD step 4 — technical FEAT plan and decisions. Use when clarification and check are complete. Not for task breakdown (skill sdd-tasks).
argument-hint: "FEAT-nnn [technical constraints]"
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

Process: `../sdd-constitution/references/sdd-process.md`.

## 1. Confirm readiness

Require `status: clarified` and an `sdd-check` report without a security/integrity failure. Read the actual modules/files plus repository rules; do not infer structure from the desired design.

## 2. Write the FEAT Plan

Cover:

- domain aggregates/value objects/events and protected invariants;
- client, server, protocol and adapter boundaries;
- changed messages/endpoints with compatibility and protocol-version effect;
- tables/columns, `V<n>__slug.sql`, indexes, transaction and idempotency;
- feature flag name, default and off behavior, or why none is needed;
- each acceptance criterion's test type/location;
- logs/metrics, hypotheses with validation (at most three load-bearing risks, each `Fails if <condition>` with its cheapest test; one that needs code becomes an `sdd-spike`), each external API with its exact signature and the source read this session, dependencies and blockers.

## 3. Record decisions

A choice with a rejected reasonable alternative gets a decision record (`DEC-nnn`, or the prefix of its kind when `docs/spec/spec.md` declares `decision_kinds`) with `status: proposed`; an already-approved product choice records its source and may be approved. Do not hide a kit-rule exception in prose—record a blocker or explicit DEC.

## 4. Check restraint and consistency

Do not add queue/cache/service/layer without demonstrated need. Ensure every criterion has a planned proof, then set `status: planned`, update History and run `sdd-check` with no critical/high findings.

Done when: the Plan names real files/boundaries, every criterion has a test, decisions have DEC or justification, and the check is unblocked.
