---
name: testing
description: Test policy and gates. Use when setting coverage/mutation gates or deciding what not to test. Not for legacy tests (skill characterization-tests).
triggers:
  - user
  - model
allowed-tools:
  - read
  - grep
  - glob
  - exec
  - edit
---

# Testing

## 1. Classify the behavior

Domain rules involving business logic, money, inventory, rewards, battle or authorization require 100% line and branch coverage plus mutation score ≥80%. These gates are never reduced.

Outside the domain, require one executable test for each non-trivial branch, parser, rule-bearing mapping or translated adapter behavior; trivial getters, records, constructors, one-to-one mappings and framework wiring remain untested.

## 2. Define behavior before implementation

- Bug: add a test that reproduces the symptom and fails for the right reason before the fix.
- Feature: the failing acceptance/domain test defines the behavior that makes the task done.
- Business rule: use a parameterized valid/boundary/invalid case table.

## 3. Choose the proof level

1. Unit: domain without framework or I/O; fake ports only.
2. Integration: real adapter boundary with a happy and sad case.
3. Contract: versioned client/server examples validated on both sides.
4. End-to-end/smoke: few tests around the vertical slice.

Money, inventory and reward operations also require idempotency (same command twice, one effect) and concurrency (competing operations, one valid outcome) tests.

## 4. Wait for evidence, not time

Never use `Thread.sleep`, `time.sleep` or an engine timer to let a test catch up. Wait for the observable condition with a bounded timeout and an error naming the missing condition.

## 5. Keep assertions behavioral

Do not test getters, framework behavior or that collaborator X was called. Assert the externally observable result or state transition. A failing test is fixed with code/test correction, never disabling it.

## 6. Run gates

Run the narrow relevant test first, then the repository gate. Investigate unit tests over one second or integration tests over ten seconds instead of normalizing the delay.

Done when: required domain percentages and mutation pass, every non-trivial non-domain change has one proof, integrations have happy/sad coverage, and no test sleeps or asserts implementation calls.
