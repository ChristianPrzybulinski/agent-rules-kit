---
name: testing
description: Test policy. Use when choosing or reviewing tests, setting coverage/mutation gates or before refactoring legacy or ported code. Not for verdicts (skill review).
argument-hint: "[legacy class/method or flow to characterize | empty]"
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

Domain rules involving business logic, money, inventory, rewards, game rules or authorization require 100% line and branch coverage plus mutation score ≥80%. These gates are never reduced.

Every surviving mutant on a changed line is killed by a new assertion, deleted as dead code, or named as equivalent in the PR body; a green 80% gate does not excuse it.

Outside the domain, require one executable test for each non-trivial branch, parser, rule-bearing mapping or translated adapter behavior; trivial getters, records, constructors, one-to-one mappings and framework wiring remain untested.

GDScript (Godot): no line, branch or mutation percentage gate; the coverage and mutation tools below stay advisory (owner, 2026-11-13, KIT-034 and KIT-035), and the § 5 empty-return check stands in for a gate. Every game rule (combat, inventory, movement validation, economy, rewards) lives in a pure `RefCounted` class with `class_name`, built with `.new()` and tested without a `SceneTree` (no `add_child`, no autoload, no `get_node`; inject the clock and the RNG). Scene tests (gdUnit4 scene runner, GUT `add_child_autofree`) are integration tests: few, around a `.tscn` contract. CI fails when the runner is absent or zero tests execute.

Before a PR or a completion verdict that touches a `.gd` game rule, run from the Godot project folder `python3 ~/.ai-kit/platforms/tools/gd_coverage.py --base <base> --json <cov.json>`, then `python3 ~/.ai-kit/platforms/tools/gd_mutation.py --base <base> --coverage <cov.json>`; both run the project's gdUnit4 suites on a `git archive` copy and are advisory. Coverage prints `lines C/T branches C/T` per changed function. The copy gains a writer autoload and every probed script calls `KitCov`, so pass `--ignore <suite or suite:test>` for each test that reads the project's own wiring (its autoloads, a script's dependencies; a line only those tests reach then counts as not covered) and `--exclude <path>` for a script a test copies into another project; exit 2 means the run did not count (red suite, timeout, missing godot, gdUnit4 or gdtoolkit), never 0 %. Mutation prints each surviving mutant, and `--coverage` lists a mutant on a never-run line as "no coverage" without a run. Its cache keeps each result under the function's text and its selected test files, so a rerun with neither changed starts no Godot; a change outside them (the rest of the file, the project, Godot's version) is not in that key, so rerun then with `--no-cache`.

Parity: every quality check one language has (coverage, mutation, complexity, duplication), the other gets with the same rule; when no tool exists the kit builds one, and each tool stays advisory until its false-positive rate is measured.

## 2. Define behavior before implementation

- Bug: add a test that reproduces the symptom and fails for the right reason before the fix. When the test came after the fix, revert the fix once and see the test fail for the stated reason.
- Feature: write the acceptance or domain test before the implementation exists, run it, and keep its failing line for the PR's Proof; that test defines the behavior that makes the task done.
- Business rule: use a parameterized valid/boundary/invalid case table.
- Legacy or ported code with no spec (refactor or rebalance): pin its current behavior first with characterization tests, `references/characterization.md`; never fix behavior while pinning it.

## 3. Choose the proof level

1. Unit: domain without framework or I/O; fake ports only.
2. Integration: real adapter boundary with a happy and sad case.
3. Contract: versioned client/server examples validated on both sides.
4. End-to-end/smoke: few tests around the vertical slice.

Money, inventory and reward operations also require idempotency (same command twice, one effect) and concurrency (competing operations, one valid outcome) tests.

## 4. Wait for evidence, not time

Never use `Thread.sleep`, `time.sleep` or an engine timer to let a test catch up. Wait for the observable condition with a bounded timeout and an error naming the missing condition.

## 5. Keep assertions behavioral

Do not test getters, framework behavior or that collaborator X was called. Assert the externally observable result or state transition. A failing test is fixed with code/test correction, never by disabling it; a golden file, snapshot, threshold or case list changes only for an intended behavior change the PR names.

- Call the code through the public entry its user uses (public method, port, message or scene contract) and assert what that user sees; never reach into a private helper.
- A test that would still pass if every function under test returned null, zero or empty, or if the rule it names were removed, proves nothing: rewrite it with the expected value, or delete it. The expected value comes from the spec or a worked example, never from running the code under test (characterization excepted); a sad-path test passes every earlier guard (auth, validation, flag) and asserts the specific error its name promises.
- A test asserts what the spec or task asked for; one that pins behavior nobody asked for is deleted, or the behavior goes into the spec first (characterization excepted).
- Each test builds and removes its own data and passes alone and in any order; a test that sets shared state (a database row, a static field, a file) resets it.
- When an honest test is impractical, write none: record the manual proof (the command or steps and what was observed) in the PR body instead.

## 6. Run gates

Size the proof by what the change can affect, never by file extension: agent instructions, permissions, workflows and executable config are code when they change runtime or security behavior. Unknown impact takes the higher row.

| Impact | Proof before "done" |
|---|---|
| Docs only: prose, specs, comments; no runtime, permission or workflow effect | Read the diff; run the repository's doc, schema, link or generator checks. No code suite. |
| Bounded code: one module, no shared boundary | Reproduce the failure first; run the affected tests; add a regression test where it guards meaningful behavior; one independent review. |
| Shared integration, authorization, persistence or migration | Boundary and negative tests, then the broad affected suite, then one independent review; owner and security approvals stay. |

Run the narrow checks and the consumer audit first and the broad suite last, once. A recorded result stays valid while the files, dependencies, config, environment and assumptions it ran on are unchanged; a new commit hash alone invalidates nothing. After a correction, re-run what the delta touches and the assumptions it changes; repeat the broad suite only when the delta reaches what it covered. The § 1 domain gates apply in every row. A green run counts only when the runner's summary shows the expected tests executed, not skipped or zero (recheck after a filter such as `-k` or `-Dtest`); a generated file or export is checked by its content, not its exit code. Investigate unit tests over one second or integration tests over ten seconds instead of normalizing the delay.

Done when: required domain percentages and mutation pass (JVM) or every GDScript rule has a scene-free test, every non-trivial non-domain change has one proof, integrations have happy/sad coverage, no test sleeps or asserts implementation calls, no test passes on empty returns, and every surviving mutant on a changed line is killed, deleted or named.
