---
name: clean-code
description: Code rules for names, functions and comments. Use when naming, editing functions, writing comments or reviewing code. Not for test policy (skill testing).
triggers:
  - user
  - model
allowed-tools:
  - read
  - grep
  - glob
  - edit
---

# Clean Code

## 1. Read local conventions

Inspect neighboring code plus `.editorconfig`, `pom.xml` or `project.godot`. Those files own formatting and lint settings; never restate their configuration in rules or comments.

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

## 5. Control file growth

- Aim for 200–400 lines per feature file; 800 is the maximum before mandatory decomposition.
- Fewer files win when cohesion remains high. Delete dead code before adding another abstraction.

## 6. Review the diff

Search callers before renaming or changing behavior. Run the repository formatter/linter and its relevant tests; report literal failures rather than adding suppression.

Done when: names are literal, functions have one purpose, comments explain only why, errors remain visible, and touched files respect the size ceiling.
