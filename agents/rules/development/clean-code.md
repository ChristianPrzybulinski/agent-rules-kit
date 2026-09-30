---
description: Details of Clean Code (names, functions, classes, comments, tests). Load when writing or reviewing production code; the summary is already in AGENTS.md.
trigger: model_decision
---

# Clean Code

## Names

- **English, always** — identifiers, packages, files, folders, Javadoc, comments, log and error messages. Mixed language in code is a review bug.
- Short, purposeful, literal: `balance`, `findByPlayer`, `BattleTurn`. The name says what it is, not how it was made or who uses it.
- Forbidden: non-universal abbreviation (`usr`, `qty`, `mgr`), decorative suffix (`Manager`, `Helper`, `Util`, `Data`, `Info`, `Impl` without a second implementation), type prefix (`strName`, `IRepository`), magic number without a constant.
- Boolean reads as a question (`isActive`, `hasStock`); collection in plural (`items`); method with a verb (`apply`, `find`, `reserve`); class with a noun.
- One concept, one name: do not alternate `player`/`user`/`character` for the same thing. The project glossary (`docs/spec/spec.md`) is the source.

## Functions and methods

- Short: ideally up to 20 lines; recommended maximum 40.
- Do **one single thing** (Single Responsibility Principle).
- Maximum 3-4 parameters; beyond that, use objects/records/DTOs.
- Avoid hidden side effects.

## Classes and modules

- High cohesion; low coupling.
- Open for extension, closed for modification (OCP).
- Prefer composition over inheritance.
- Do not expose internal state unnecessarily.

## Control and flow

- Avoid deep nesting (>3 levels). Extract functions or use early returns.
- Handle errors explicitly, not with special return codes.
- Do not ignore exceptions/errors without a documented reason.

## Comments

- Code must be self-explanatory.
- Comments only to explain the "why", not the "what".
- Do not leave dead commented-out code in the repository.

## Tests

- Code without tests is code that does not work.
- Name tests descriptively: `should_<behavior>_when_<condition>`.
- One assert per test ideally; at most one concept per test.
