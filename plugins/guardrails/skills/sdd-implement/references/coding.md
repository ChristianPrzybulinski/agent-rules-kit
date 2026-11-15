---
description: "Designing and closing a code change: read the flow, the first sufficient rung, one decision in one place, docs. Load at Green."
kind: detail
---

# Coding

The Green and Refactor steps of the task cycle (`sdd-implement` § 2) and any plain code change. Line-level always/never (names, function size, comments, errors, file size, generated files): rule `code.md`.

## 1. Read local conventions and the whole touched flow

Inspect the neighbouring code plus `.editorconfig`, `pom.xml` or `project.godot`, and locate callers, neighbouring implementations and existing dependencies before selecting a solution. Those files own formatting and lint settings; never restate their configuration in rules or comments. The ladder below reduces the implementation, not the investigation.

## 2. Stop at the first sufficient rung

1. Does the requested behavior need to exist now?
2. Does the repository already contain the helper, type or pattern?
3. Does the standard library solve it?
4. Does the database, engine or platform provide it natively?
5. Does an already-installed dependency solve it?
6. Does the correct implementation fit clearly in one line?
7. Only then write the minimum new code.

Choose the higher rung when two work; never trade correctness at an edge case for fewer characters. Before writing a reusable utility or adding a dependency, follow `dependency-search.md`.

## 3. Design the change before the edit

- One decision (rule, threshold, mapping) lives in one place; every other site reads it from there.
- A new or changed function that repeats existing code is merged into one owner every caller uses, or the PR names why the copy stays; in GDScript, `python3 ~/.ai-kit/platforms/tools/gd_duplicates.py --base <base>` lists the pairs at 0.82 or more (advisory).
- Get the data shape right before the logic: a shape that holds only valid states removes the branches that would repair it.
- A new requirement is not bolted onto the old design: build the smallest edit of the design you would have made had the requirement been there from the start, and deliver it in pieces. A second special case for the same root cause means the design is wrong: reopen it instead of adding a third.
- When work is not obvious at a glance, do one unit by hand, then make a tool reproduce it (the hand-done unit is the tool's test); do first what helps every later step.

## 4. Review your own diff

- Fewer files win when cohesion remains high. Remove what the change makes unnecessary (dead code, flag, special case, layer) before adding another abstraction; a simplification removes more than it adds, and moving logic into a wrapper is not one.
- Report a ceiling you skipped as `[code] → skipped: X; add when Y.`; delete explanation that exceeds the simple change unless the user asked for a report.

## 5. Close the docs in the same PR

Run the closure checklist in `living-docs.md` (README and `AGENTS.md` commands, CHANGELOG, public API docs, decision, debt and feature records, prose for people).

Done when: the solution stops at the earliest safe rung with no speculative dependency or abstraction, each decision lives in one place, a deliberate ceiling records its evolution trigger, and every applicable living-docs item is updated in the same PR.
