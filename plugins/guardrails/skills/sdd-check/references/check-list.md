---
description: Quality checklist for sdd-check step 2 (testability, security and integrity, data, compatibility and operation, feedback) with the grading rule.
kind: detail
---

# Check list

Grade each item pass / fail / not-applicable; a fail carries its evidence `path:line`, a pass or not-applicable item is listed by id only; a security or integrity fail is `critical`. The functional scope (`NEED-nnn`) grades Q1 against each REQ's Verification, Q2–Q4, Q7 and Q12; the full scope (`FEAT-nnn`) grades every item, Q1 against the FEAT's criteria.

## Testability and completeness

- Q1. Each criterion (full) or REQ Verification (functional) has happy/sad behavior, as examples and counterexamples, and names its unit/integration/contract/e2e proof; in the full scope, every name, type, exact text or order a test will assert appears in the FEAT.
- Q2. Invalid input, missing resource, conflict, timeout and permission errors are defined.
- Q3. Network reconnect/retry and numeric size/frequency/quantity limits are explicit or hypotheses.

## Security and integrity

- Q4. Actor and per-entity authorization are specified.
- Q5. Server validation versus client intent is explicit (full scope only).
- Q6. Money/inventory/reward effects define idempotency and transaction boundaries (full scope only).
- Q7. Personal data, retention and non-production test data are identified.

## Data, compatibility and operation

- Q8. Schema changes include migration and existing-data handling.
- Q9. Contract changes declare compatibility and protocol-version effect.
- Q10. Client platform impact is addressed.
- Q11. Logs/metrics, feature flag/off behavior and documentation changes are listed.

## Feedback

- Q12. Each player or user action in a journey or process step names its feedback (visual, sound or message) and when it appears (at once, when a state ends, on failure): a game's hit flash and sound, a business form's loading, success and error states (`../../sdd-clarify/references/processes.md` § Write).
