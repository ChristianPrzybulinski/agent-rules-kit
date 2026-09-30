---
name: sdd-audit
version: "1.0"
description: SDD step 4 — spec quality audit with a checklist - testability, completeness, security, data, errors, compatibility, observability. Produces a gap list to fix before planning. Use when the FEAT is clarificada.
argument-hint: "FEAT-nnn"
triggers:
  - user
  - model
allowed-tools:
  - read
  - glob
  - grep
  - write
---

# SDD 4 — Audit (checklist)

Equivalent to spec-kit's `checklist`. Produces `docs/spec/features/FEAT-nnn.checklist.md` (or an *Audit* section in the FEAT, per the project) with ✓/✗/n.a. items and justification.

## Checklist

**Testability**
- [ ] Each criterion has a happy and a sad path.
- [ ] Each criterion states the test type that proves it (unit/integration/contract/e2e).
- [ ] Test data described without real personal data.

**Completeness**
- [ ] Error states defined (invalid input, missing resource, conflict, timeout, no permission).
- [ ] Reconnect/retry behavior defined, if it involves the network.
- [ ] Limits (size, frequency, quantity) numeric or `[HYPOTHESIS]`.

**Security and integrity**
- [ ] Who can execute (authz per action and entity).
- [ ] What the server validates vs. what it trusts from the client (nothing).
- [ ] Operation with money/inventory/reward → idempotency and transaction described.
- [ ] Personal data involved listed; retention defined.

**Data and compatibility**
- [ ] Schema change → migration mentioned; existing data handled.
- [ ] Contract change → compatible/incompatible decided; `protocol_version` impacted?
- [ ] Windows and macOS considered, if it touches the client.

**Operation**
- [ ] What to log/measure to know it works in production.
- [ ] Feature flag needed? name and off behavior.

**Documentation**
- [ ] Docs to update listed (README, CHANGELOG, protocol, glossary).

## Output

✗ items become a gap list with an action (go back to `clarify`, edit the spec, or an explicit `[HYPOTHESIS]`). A security/integrity gap ✗ → **blocks** `plan`.
