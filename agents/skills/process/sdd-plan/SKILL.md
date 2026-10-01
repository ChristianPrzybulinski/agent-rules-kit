---
name: sdd-plan
version: "1.0"
description: SDD step 5 — technical plan for a clarified, audited FEAT - modules touched, domain model, contract, persistence/migration, feature flag, test strategy, risks; creates DEC-nnn for decisions with a rejected alternative. Status becomes planned. Use after sdd-audit, before sdd-tasks. Do not use to break the plan into tasks (skill sdd-tasks) or before clarify and audit are done.
argument-hint: "FEAT-nnn [technical constraints]"
triggers:
  - user
allowed-tools:
  - read
  - glob
  - grep
  - edit
  - write
  - exec
---

# SDD 5 — Plan

Prerequisite: `status: clarified`, audit without a security ✗. References: skills `clean-architecture`, `ddd-and-patterns`, `java-standards`, `godot-standards`, the repo's `AGENTS.md`, `docs/spec/decisions/`.

## Steps

1. Read existing code in the touched areas (do not presume structure). List real files/modules.
2. Write the **Plan** section in the FEAT:
   - **Domain**: new or changed aggregates/VOs/events; invariants the server protects.
   - **Boundaries**: what lives on the client (presentation/intent) vs server (validation/result) vs protocol.
   - **Contract**: new or changed messages/endpoints, with a minimal example; compatible or incompatible (`protocol_version`).
   - **Persistence**: tables/columns, `V<n>__slug.sql` migration, indexes, transaction, idempotency key if applicable.
   - **Feature flag**: name, default, off behavior — or "not needed" with a reason.
   - **Tests**: per acceptance criterion → test type and where it lives. Domain: case table.
   - **Observability**: logs/metrics that prove it works.
   - **Risks and hypotheses**: each `[HYPOTHESIS]` with how/when to validate.
   - **Dependencies/blockers**: other FEATs, tools, pending decisions.
3. Every choice with a rejected reasonable alternative → `DEC-nnn-slug.md` (template `decision.md`), state `proposed`; reference it in the FEAT. A decision already approved by the product → `approved` with a source.
4. Plan violates a kit/repo rule → do not plan a workaround: record `[BLOCKER]` or propose an explicit `DEC`.
5. `status: planned`; *History* updated; `sdd-analyze FEAT-nnn` must pass with no critical/high.

## Completion criteria

- Every acceptance criterion has a planned test.
- No relevant technical decision without a `DEC` or a 1-line justification.
- Does not introduce a layer/infra (queue, cache, service) without a demonstrated need in the plan.
