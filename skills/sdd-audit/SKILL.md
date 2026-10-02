---
name: sdd-audit
description: SDD step 4 — spec quality checklist. Use when a clarified FEAT needs testability, security and completeness checks. Not for consistency (skill sdd-analyze).
argument-hint: "FEAT-nnn"
triggers:
  - user
  - model
allowed-tools:
  - read
  - glob
  - grep
  - edit
---

# SDD 4 — Audit

Process: `../sdd-constitution/references/sdd-process.md`.

## 1. Create the checklist

Use `docs/spec/features/FEAT-nnn.checklist.md` or the project's Audit section. Mark each item pass/fail/not-applicable with evidence.

## 2. Audit testability and completeness

- Each criterion has happy/sad behavior and names its unit/integration/contract/e2e proof.
- Invalid input, missing resource, conflict, timeout and permission errors are defined.
- Network reconnect/retry and numeric size/frequency/quantity limits are explicit or hypotheses.

## 3. Audit security and integrity

- Actor and per-entity authorization are specified.
- Server validation versus client intent is explicit.
- Money/inventory/reward effects define idempotency and transaction boundaries.
- Personal data, retention and non-production test data are identified.

## 4. Audit data, compatibility and operation

- Schema changes include migration and existing-data handling.
- Contract changes declare compatibility and protocol-version effect.
- Client platform impact is addressed.
- Logs/metrics, feature flag/off behavior and documentation changes are listed.

## 5. Route gaps

Turn each failure into a concrete clarification, spec edit or measurable hypothesis. Security/integrity failures block `sdd-plan`.

Done when: every checklist item has evidence, each failure has an owner/action, and no security/integrity gap can enter planning.
