---
description: Always/never constraints for test code; which tests a change needs, the Red step and the gates are in the sdd-implement tdd and test-gates references.
trigger: glob
globs:
  - "**/tests/**"
  - "**/test/**"
  - "**/*_test.gd"
  - "**/*Test.java"
  - "**/test_*.py"
  - "**/*_test.py"
paths:
  - "**/tests/**"
  - "**/test/**"
  - "**/*_test.gd"
  - "**/*Test.java"
  - "**/test_*.py"
  - "**/*_test.py"
---

Always/never for test code. Which tests a change needs and the Red step: skill `sdd-implement`, reference `tdd.md`; coverage, mutation and the impact table of checks before "done": `test-gates.md`; legacy or ported code with no spec: `characterization.md`.

- Never: `Thread.sleep`, `time.sleep` or an engine timer to let a test catch up; wait for the observable condition with a bounded timeout and an error that names the missing condition.
- Always: call the code through the entry its user uses (public method, port, message or scene contract) and assert what that user sees; never a getter, framework behavior, a private helper or that collaborator X was called.
- Never: a test that would still pass if every function under test returned null, zero or empty, or if the rule it names were removed; rewrite it with the expected value or delete it.
- Always: the expected value comes from the spec or a worked example, never from running the code under test (characterization excepted).
- Always: a sad-path test passes every earlier guard (authorization, validation, flag) and asserts the specific error its name promises.
- Always: a business rule takes a parameterized valid/boundary/invalid case table.
- Always: a test asserts what the spec or task asked for; one that pins behavior nobody asked for is deleted, or the behavior enters the spec first (characterization excepted).
- Never: disable, skip or focus a test (`@Disabled`, `.only`, `unittest.skip`) or loosen an assertion, threshold or timeout to go green; a golden file, snapshot, threshold or case list changes only for an intended behavior change the PR names.
- Always: each test builds and removes its own data and passes alone and in any order; a test that sets shared state (a database row, a static field, a file) resets it.
- Always: domain tests run without database, network, UI or framework context, with fakes at ports; never mock an entity.
- Always: GDScript game rules are tested scene-free (a `RefCounted` built with `.new()`, clock and RNG injected); scene tests are few integration tests around a `.tscn` contract.
- Always: money, inventory and reward operations also get an idempotency test (same command twice, one effect) and a concurrency test (competing operations, one valid outcome).
- Always: a green run counts only when the runner's summary shows the expected tests executed, not skipped or zero (recheck after a filter such as `-k` or `-Dtest`).
- Always: investigate a unit test over one second or an integration test over ten seconds instead of normalizing the delay.
- Always: when an honest test is impractical, write none and record the manual proof (the command or steps and what was observed) in the PR body.
