---
name: characterization-tests
version: "1.1"
description: Tests that pin current behavior of legacy or ported code. Use when refactoring or rebalancing a rule with no spec. Not for new behavior (skill testing).
argument-hint: "[legacy class/method | flow: damage, evolution, encounter...]"
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

# Characterization Tests

## 1. Delimit one rule

- Select one input-to-output rule such as damage, capture chance, XP or price.
- If I/O obscures it, introduce only the smallest seam for RNG, clock or repository without changing behavior.
- Record the current source at `file:line` and any original port source actually read.

## 2. Build discriminating cases

- Cover zero, negative, maximum, overflow, empty and null where the code accepts them.
- Add values where truncation and rounding diverge.
- Inject a fixed RNG seed or sequence; sample a distribution only when the formula cannot be read.
- Put tables in `src/test/resources/characterization/<rule>.csv`; use JUnit `@CsvFileSource` above five cases.
- Preserve surprising behavior with `// CHARACTERIZATION: current behavior, not validated as correct` and link a `DEBT-xxx` when relevant.

## 3. Prove the baseline

- Name the class `<Rule>CharacterizationTest` and methods `given<input>_returns<currentOutput>`.
- Run `./mvnw -q -pl <module> test -Dtest=<Class>` against the untouched behavior and capture literal output.
- A test that starts red is not characterization; resolve the observation or fixture first.

## 4. Compare an original when available

- If executable, run the same fixture against both versions and record `legacy-expected | current | decision`.
- If not executable, transcribe the formula beside the test and mark divergence `[HYPOTHESIS]` until decided.

## 5. Hand off deliberate change

- Link the test class from the motivating FEAT or DEC.
- Put product-significant divergence in a proposed `DEC-xxx` with both options and impact.
- Refactor or rebalance only after the baseline is green; each intentional output change updates its case with commit justification.

## 6. Guard the observation

- Do not fix behavior during characterization or mock the rule being characterized.
- Historical coverage or portability percentages do not replace an executable baseline.

Done when: the current rule is reproducibly green, sources and surprising cases are recorded, and later behavior changes must alter an explicit expectation.
