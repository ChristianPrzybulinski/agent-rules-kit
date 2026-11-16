---
description: The Red test for a bug, a feature, a business rule or legacy code, and the proof level each behavior needs. Load at Red.
kind: detail
---

# Test first

The Red step of the task cycle (`sdd-implement` § 2) and any change that adds behavior. Always/never for the test code itself: rule `tests.md`; which gates run before "done": `test-gates.md`.

## 1. Define behavior before implementation

- Bug: add a test that reproduces the symptom and fails for the right reason before the fix. When the test came after the fix, revert the fix once and see the test fail for the stated reason.
- Feature: write the acceptance or domain test from the REQ's example or counterexample, or the row's acceptance criterion, before the implementation exists; run it and keep its failing line for the PR's `## Red` section. That test defines the behavior that makes the task done.
- Business rule: a parameterized valid/boundary/invalid case table.
- Legacy or ported code with no spec (refactor or rebalance): pin its current behavior first with characterization tests (`characterization.md`); never fix behavior while pinning it.

The failing line must name the missing behavior: an import error, a typo or a fixture error is not Red. Exceptions, named in `## Red`: a characterization test of existing behavior, or a manual proof with the reason no honest test exists.

## 2. Choose the proof level

1. Unit: domain without framework or I/O; fake ports only.
2. Integration: the real adapter boundary with a happy and a sad case.
3. Contract: versioned client/server examples validated on both sides.
4. End-to-end or smoke: few tests around the vertical slice.

Money, inventory and reward operations also need an idempotency test (same command twice, one effect) and a concurrency test (competing operations, one valid outcome).

## 3. Keep the assertion honest

- Assert the externally observable result or state transition through the entry its user uses; the expected value comes from the spec or a worked example, never from running the code under test (characterization excepted).
- A test that would still pass if every function under test returned null, zero or empty, or if the rule it names were removed, proves nothing: rewrite it with the expected value, or delete it. Until GDScript has a coverage and mutation gate, this check stands in for them.
- A sad-path test passes every earlier guard (authorization, validation, flag) and asserts the specific error its name promises.

Done when: every new behavior has a test that failed first for the stated reason (or `## Red` names the exception), each test sits at the lowest proof level that shows the behavior, and no assertion could pass on an empty return.
