---
description: Coverage and mutation gates, the GDScript advisory tools and the impact table that sizes checks before done. Load at Prove.
kind: detail
---

# Test gates

The Prove step of the task cycle (`sdd-implement` § 2), the review depth tiers (skill `review`) and the global rule "run the checks the change's impact requires" all read § 3.

## 1. Classify the behavior

- Domain rules involving business logic, money, inventory, rewards, game rules or authorization require 100% line and branch coverage plus a mutation score of at least 80% (JVM). These gates are never reduced. Every surviving mutant on a changed line is killed by a new assertion, deleted as dead code, or named as equivalent in the PR body; a green 80% gate does not excuse it.
- Outside the domain, one executable test for each non-trivial branch, parser, rule-bearing mapping or translated adapter behavior; trivial getters, records, constructors, one-to-one mappings and framework wiring stay untested.
- Parity: every quality check one language has (coverage, mutation, complexity, duplication), the other gets with the same rule; when no tool exists the kit builds one, and each tool stays advisory until its false-positive rate is measured.

## 2. GDScript

No line, branch or mutation percentage gate; the tools below stay advisory (owner, 2026-11-13, KIT-034 and KIT-035), and the empty-return check of `tdd.md` § 3 stands in for a gate. Every game rule lives in a pure `RefCounted` class with `class_name`, tested without a `SceneTree`; CI fails when the runner is absent or zero tests execute.

Before a PR or a completion verdict that touches a `.gd` game rule, run from the Godot project folder `python3 ~/.ai-kit/platforms/tools/gd_coverage.py --base <base> --json <cov.json>`, then `python3 ~/.ai-kit/platforms/tools/gd_mutation.py --base <base> --coverage <cov.json>`; both run the project's gdUnit4 suites on a `git archive` copy.

- Coverage prints `lines C/T branches C/T` per changed function. The copy gains a writer autoload and every probed script calls `KitCov`, so pass `--ignore <suite or suite:test>` for each test that reads the project's own wiring (its autoloads, a script's dependencies; a line only those tests reach then counts as not covered) and `--exclude <path>` for a script a test copies into another project.
- Exit 2 means the run did not count (red suite, timeout, missing godot, gdUnit4 or gdtoolkit), never 0 %.
- Mutation prints each surviving mutant; `--coverage` lists a mutant on a never-run line as "no coverage" without a run. Its cache keys each result on the function's text and its selected test files, so a rerun with neither changed starts no Godot; after a change outside them (the rest of the file, the project, Godot's version) rerun with `--no-cache`.

## 3. Size the checks by impact

Size the proof by what the change can affect, never by file extension: agent instructions, permissions, workflows and executable config are code when they change runtime or security behavior. Unknown impact takes the higher row.

Locally the implementer runs only the TDD loop (the unit and integration tests covering the changed files) and the linters. CI runs the broad suite and every other layer on the pushed head, and its result is the proof the review reads; where the repository runs no CI on each push, the project's gate command or its loop's gate stands in.

| Impact | Proof before "done" |
|---|---|
| Docs only: prose, specs, comments; no runtime, permission or workflow effect | Read the diff; run the repository's doc, schema, link or generator checks. No code suite. |
| Bounded code: one module, no shared boundary | Reproduce the failure first; run the affected tests; add a regression test where it guards meaningful behavior; one independent review. |
| Shared integration, authorization, persistence or migration | Boundary and negative tests locally, the broad affected suite in CI, then one independent review; owner and security approvals stay. |

- Run the narrow checks and the consumer audit locally; the broad suite runs once, in CI, on the pushed head. The § 1 domain gates apply in every row.
- A recorded result stays valid while the files, dependencies, config, environment and assumptions it ran on are unchanged; a new commit hash alone invalidates nothing. After a correction, re-run locally what the delta touches and the assumptions it changes; CI repeats the rest on the new head.
- A green run counts only when the runner's summary shows the expected tests executed, not skipped or zero (recheck after a filter such as `-k` or `-Dtest`); a generated file or export is checked by its content, not its exit code.

Done when: the domain percentages and mutation pass (JVM) or every GDScript rule has a scene-free test, every non-trivial non-domain change has one proof, integrations have happy and sad coverage, and the checks match the change's impact row.
