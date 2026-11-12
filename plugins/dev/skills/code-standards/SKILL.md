---
name: code-standards
description: Code names, functions, errors, YAGNI and doc closure. Use when writing or reviewing code, adding a dependency or updating docs. Not for tests (skill testing).
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

# Code Standards

## 1. Read local conventions and the whole touched flow

Inspect neighboring code plus `.editorconfig`, `pom.xml` or `project.godot`, and locate callers, neighboring implementations and existing dependencies before selecting a solution. Those files own formatting and lint settings; never restate their configuration in rules or comments. The ladder reduces the implementation, not the investigation.

## 2. Name literally

- Use one English term per concept; consult the project glossary before introducing a synonym, and add a new domain term to the glossary in the same change.
- Booleans read as questions, collections are plural, methods use verbs and classes use nouns.
- Reject type prefixes, unexplained abbreviations and decorative `Manager`, `Helper`, `Util`, `Data`, `Info` or `Impl` suffixes.

## 3. Keep functions focused

- One function performs one behavior, uses early returns and has no hidden side effects.
- Use at most three or four parameters; introduce a record/DTO when the values form one concept.
- Treat 20 lines as the target and 40 as the review threshold; split by behavior, not arbitrary chunks.
- A `match`/`switch` whose arms each make one call is fine; arms that hold logic are split into functions or become a table.
- New or changed functions target CRAP < 10 (Java) and CC ≤ 10 (GDScript); bring one above it down by splitting it, testing it or both (the one-call `match` above is exempt). `python3 ~/.ai-kit/platforms/tools/complexity.py --base <base>` lists them; its output is advisory.

## 4. Handle comments and errors

- A comment records a non-obvious reason, invariant or trade-off; delete narration and dead commented code.
- Return or throw specific errors and never swallow one.
- Prefer a visible failure to a special return code that callers can ignore.

## 5. Stop at the first sufficient rung

1. Does the requested behavior need to exist now?
2. Does the repository already contain the helper, type or pattern?
3. Does the standard library solve it?
4. Does the database, engine or platform provide it natively?
5. Does an already-installed dependency solve it?
6. Does the correct implementation fit clearly in one line?
7. Only then write the minimum new code.

Choose the higher rung when two work; never trade correctness at an edge case for fewer characters. Before writing a reusable utility or adding a dependency, follow `references/dependency-search.md`.

## 6. Reject speculative structure and protect non-negotiable behavior

- Do not add a one-implementation interface, one-product factory, future-only configuration or unrequested scaffolding. A port is justified only by external I/O, a real planned swap or a domain boundary.
- Never simplify trust-boundary validation, data-loss prevention, security/authorization, accessibility, an explicit user requirement, or domain integrity for money/inventory/reward/battle.
- For a deliberate ceiling, add `// simplified: <ceiling>; <when/how to evolve>` and create `DEBT-xxx` when the roadmap reaches it.

## 7. Control file growth and review the diff

- Aim for 200–400 lines per feature file; 800 is the maximum before mandatory decomposition.
- Fewer files win when cohesion remains high. Remove what the change makes unnecessary (dead code, flag, special case, layer) before adding another abstraction.
- Leave clear, local code alone: no drive-by refactor outside the flow the change touches.
- Search callers before renaming or changing behavior. Run the repository formatter/linter and its relevant tests; report literal failures rather than adding suppression.
- Report the ceiling with `[code] → skipped: X; add when Y.` Delete explanation that exceeds the simple change unless the user requested a report.

## 8. Design the change before the edit

- One decision (rule, threshold, mapping) lives in one place; every other site reads it from there.
- A new or changed function that repeats existing code is merged into one owner every caller uses, or the PR names why the copy stays; in GDScript, `python3 ~/.ai-kit/platforms/tools/gd_duplicates.py --base <base>` lists the pairs at 0.82 or more (advisory).
- Get the data shape right before the logic: a shape that holds only valid states removes the branches that would repair it.
- A new requirement is not bolted onto the old design: build the smallest edit of the design you would have made had the requirement been there from the start, and deliver it in pieces.
- When work is not obvious at a glance, do one unit by hand, then make a tool reproduce it (the hand-done unit is the tool's test); do first what helps every later step.

## 9. Close the docs in the same PR

Run the closure checklist in `references/living-docs.md` (README and `AGENTS.md` commands, CHANGELOG, public API docs, decision, debt and feature records, prose for people); observed code wins over a contradicting doc.

Done when: names are literal, functions have one purpose, comments explain only why, errors remain visible, touched files respect the size ceiling, the solution stops at the earliest safe rung with no speculative dependency or abstraction, any deliberate ceiling records its evolution trigger, each decision lives in one place, and every applicable living-docs item is updated in the same PR.
