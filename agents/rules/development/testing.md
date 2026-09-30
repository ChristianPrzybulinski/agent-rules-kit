---
description: Testing policy — 100% domain coverage, mutation testing, integration with happy and sad paths, what not to test. Load when creating/changing tests or configuring build gates.
trigger: model_decision
---

# Tests

## Gates (fail the build)

| Scope | Gate | Tool |
|---|---|---|
| `domain` module (business rules) | 100% line and branch | JaCoCo `check` on the module |
| `domain` module | mutation score ≥ 80% | PITest |
| Other modules | no numeric gate; **one** executable check per non-trivial logic | — |

Line coverage is necessary, not sufficient: 100% with weak asserts passes. Hence PITest on the domain.

## Outside the domain: YAGNI applies to tests

- Non-trivial logic (branch, loop, parser, mapping with a rule, adapter with translation) → **one** small test that fails if the logic breaks. Not a suite per method, not "for later" fixtures.
- Trivial (getter, `record`, 1:1 mapping, one-liner, framework wiring) → not tested.
- Adapter integration: the happy+sad pair is the minimum **and** sufficient in most cases.
- When in doubt whether it's domain: if it involves money, inventory, reward, battle, authorization — it's domain; full gate.

## Wait for a condition, never for time

- `Thread.sleep`/`await_timer`/`time.sleep` forbidden in tests to "give it time". Wait for the observable condition (`Awaitility`, `CountDownLatch`, Godot signal, polling with a short timeout). A test that needs `sleep` is testing timing, not behavior — or has a real race to investigate.
- Explicit timeout and a message that says **which** condition did not occur.

## Pyramid

1. **Unit** (domain): no Spring, no I/O, no entity mocks. Mock ports only.
2. **Integration** (adapters): real database via Testcontainers; real HTTP via `WebTestClient`/`MockMvc`. Always in pairs: **happy path + sad path** (invalid input, missing resource, conflict, timeout).
3. **Contract** (client↔server boundary): versioned message examples, validated on both sides.
4. **E2E/smoke**: few, on the vertical slice.

## Condition → action

- Fixing a bug → test that reproduces it, failing for the right reason, **before** the fix.
- New business rule → case table (valid / boundary / invalid) in `@ParameterizedTest`.
- Money, inventory, reward → idempotency test (same operation 2x = same state) and concurrency test (2 threads, 1 wins).
- Failing test → fix code or test; never `@Disabled` to go green.
- Slow test (>1s unit, >10s integration) → investigate; likely I/O where it shouldn't be.

## Naming

`should_<result>_when_<condition>()` — consistent per project. Explicit Given/When/Then structure in the body (comments or blocks). Gherkin/Cucumber only if non-devs read the specs.

## Do not test

- Getters/setters, `record`, trivial constructors.
- Framework (Spring already tests Spring).
- Implementation ("verify that X was called") instead of behavior.
