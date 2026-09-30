---
name: characterization-tests
version: "1.0"
description: Creates characterization tests that pin the CURRENT behavior of legacy or ported code (formulas, tables, RNG, rounding) before refactoring, migrating or rebalancing. Use before touching a rule whose correct behavior is not specified. Do not use to validate a new rule (that is a normal test with a spec).
argument-hint: "[legacy class/method | flow: damage, evolution, encounter...]"
triggers:
  - user
  - model
allowed-tools:
  - read
  - grep
  - glob
  - exec
---

# Characterization Tests

Goal: turn "the code does X" from `[HYPOTHESIS]` into a reproducible `[FACT]`, so that any future change is **deliberate** and visible in a test diff.

## 1. Delimit the unit

- One rule at a time: input → pure output (damage, capture chance, XP, price). If the rule depends on I/O, isolate first via a minimal seam (interface for RNG, clock, repository) — without changing behavior.
- Record the source: file:line of the current code **and**, if any, the original it was ported from (e.g.: a Lingo script). `[FACT]` only for what was read.

## 2. Generate cases

- Boundaries: zero, negative, maximum, type overflow, empty, null.
- Rounding and integer division: cases where truncate vs round diverge.
- RNG: inject a fixed seed/sequence; characterize the distribution by sampling only if the formula is not readable.
- Tables (levels, types, prices): small fixture in a file (`src/test/resources/characterization/<rule>.csv`), not inline constants.
- Surprising cases (apparent bug) go in **as they are**, with the comment `// CHARACTERIZATION: current behavior, not validated as correct` and a `DEBT-xxx` if relevant.

## 3. Write

- Name: `<Rule>CharacterizationTest`; method: `given<input>_returns<currentOutput>`.
- Parameterized (JUnit `@ParameterizedTest` + `@CsvFileSource`) when >5 cases.
- Run and confirm green on the current version: `./mvnw -q -pl <module> test -Dtest=<Class>`. Literal output in the report.

## 4. Compare with the original (when it exists)

- If the original is executable (rare): same fixture on both; a divergence is a finding, goes to the `legacy-expected / current-Java / decision` table.
- If not executable: side-by-side reading, formula transcribed in the test as a comment, divergence marked `[HYPOTHESIS]` until decided.

## 5. Close

- Motivating FEAT/DEC: link the test class under "Relations".
- Divergence needing a product decision → `DEC-xxx` `proposta` with both options and impact.
- Only after that does the refactor/rebalancing begin — and each intentional change updates the case with justification in the commit.

## Rules

- Do not "fix" behavior during characterization.
- Do not characterize by mocking the very code under test.
- Coverage/portability percentages inherited from old reports do not replace this step.
