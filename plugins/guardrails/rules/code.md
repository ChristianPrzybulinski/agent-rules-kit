---
description: Always/never constraints for GDScript, Java and Python source; how to design and close a change is in the sdd-implement coding reference.
trigger: glob
globs:
  - "**/*.gd"
  - "**/*.java"
  - "**/*.py"
paths:
  - "**/*.gd"
  - "**/*.java"
  - "**/*.py"
---

Always/never for source code. Reading the flow, the smallest sufficient change, one decision in one place and the docs closure: skill `sdd-implement`, references `coding.md` and `living-docs.md`; a new dependency: `dependency-search.md`.

- Always: read the neighbouring code, `.editorconfig` and the build file (`pom.xml`, `project.godot`, `pyproject.toml`), and find the callers and existing helpers before choosing a solution; formatting and lint settings live in those files and are never restated.
- Always: one English term per concept, taken from the project glossary; a new domain term enters the glossary in the same change. Booleans read as questions, collections are plural, methods are verbs and classes nouns.
- Never: type prefixes, unexplained abbreviations or decorative `Manager`, `Helper`, `Util`, `Data`, `Info` or `Impl` suffixes.
- Always: one behavior per function, early returns, no hidden side effect, at most three or four parameters (a record or DTO when they form one concept); 20 lines is the target and 40 the review threshold, split by behavior, not into arbitrary chunks.
- Always: a `match`/`switch` whose arms each make one call is fine; arms that hold logic become functions or a table.
- Always: a new or changed function targets CRAP < 10 where coverage is known (Java from JaCoCo, GDScript from `gd_coverage.py --json`) and CC ≤ 10 for GDScript without coverage; skill `review` runs `complexity.py`, which lists the ones above (advisory; reference `delivery-steps.md`).
- Always: one decision (rule, threshold, mapping) lives in one place and every other site reads it there; a new function that repeats existing code is merged into one owner, or the PR names why the copy stays (skill `sdd-implement` runs `gd_duplicates.py`, which lists GDScript pairs, advisory; reference `coding.md`).
- Always: a comment states a non-obvious reason, invariant or trade-off, kept only if deleting it loses an answer the code cannot give; never narration, dead commented code or a reference to the PR, review, task or a previous version.
- Never: swallow an error; return or throw a specific one, and prefer a visible failure to a special return value a caller can ignore.
- Never: a one-implementation interface, one-product factory, future-only configuration or unrequested scaffolding; a port needs external I/O, a real planned swap or a domain boundary.
- Never: simplify trust-boundary validation, data-loss prevention, security or authorization, accessibility, an explicit requirement or a money, inventory, reward or game-rule invariant. A deliberate ceiling carries `// simplified: <ceiling>; <when/how to evolve>` and a `DEBT-nnn` when the roadmap reaches it.
- Always: 200-400 lines per feature file, 800 at most before a split; remove what the change makes unnecessary (dead code, flag, special case, layer) before adding an abstraction, and count moving logic into a wrapper as no simplification.
- Always: search the production callers before renaming, deleting or changing behavior.
- Never: edit a generated file (a `GENERATED`/`DO NOT EDIT` header or a path the project lists); change its source or generator and rerun it.
- Always: run the repository formatter, linter and the affected tests; report a literal failure instead of adding a suppression.
- Always: a ceiling you skip is reported as `[code] → skipped: X; add when Y.`
