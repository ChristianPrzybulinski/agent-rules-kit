---
name: code-standards
description: Names, functions, comments, errors and the YAGNI ladder. Use when writing or reviewing code or adding a dependency. Not for test policy (skill testing).
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

- Use one English term per concept; consult the project glossary before introducing a synonym.
- Booleans read as questions, collections are plural, methods use verbs and classes use nouns.
- Reject type prefixes, unexplained abbreviations and decorative `Manager`, `Helper`, `Util`, `Data`, `Info` or `Impl` suffixes.

## 3. Keep functions focused

- One function performs one behavior, uses early returns and has no hidden side effects.
- Use at most three or four parameters; introduce a record/DTO when the values form one concept.
- Treat 20 lines as the target and 40 as the review threshold; split by behavior, not arbitrary chunks.

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
- Fewer files win when cohesion remains high. Delete dead code before adding another abstraction.
- Search callers before renaming or changing behavior. Run the repository formatter/linter and its relevant tests; report literal failures rather than adding suppression.
- Report the ceiling with `[code] → skipped: X; add when Y.` Delete explanation that exceeds the simple change unless the user requested a report.

Done when: names are literal, functions have one purpose, comments explain only why, errors remain visible, touched files respect the size ceiling, the solution stops at the earliest safe rung with no speculative dependency or abstraction, and any deliberate ceiling records its evolution trigger.
