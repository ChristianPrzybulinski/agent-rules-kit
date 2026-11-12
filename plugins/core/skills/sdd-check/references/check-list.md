---
description: Quality checklist for sdd-check step 2 (testability, security and integrity, data, compatibility and operation) with the grading rule.
kind: detail
---

# Check list

Grade each item pass / fail / not-applicable with evidence `path:line`; a security or integrity fail is `critical`.

## Testability and completeness

- Q1. Each criterion has happy/sad behavior and names its unit/integration/contract/e2e proof; every name, type, exact text or order a test will assert appears in the FEAT.
- Q2. Invalid input, missing resource, conflict, timeout and permission errors are defined.
- Q3. Network reconnect/retry and numeric size/frequency/quantity limits are explicit or hypotheses.

## Security and integrity

- Q4. Actor and per-entity authorization are specified.
- Q5. Server validation versus client intent is explicit.
- Q6. Money/inventory/reward effects define idempotency and transaction boundaries.
- Q7. Personal data, retention and non-production test data are identified.

## Data, compatibility and operation

- Q8. Schema changes include migration and existing-data handling.
- Q9. Contract changes declare compatibility and protocol-version effect.
- Q10. Client platform impact is addressed.
- Q11. Logs/metrics, feature flag/off behavior and documentation changes are listed.
