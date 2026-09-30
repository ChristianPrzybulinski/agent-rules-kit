---
description: Rules for documentation, changelog, versioning and ADRs. Load when editing README, CHANGELOG, ADR or versioning.
trigger: model_decision
---

# Documentation

## Language

- Every written artifact (README, CHANGELOG, spec, ADR/DEC, comment, commit, file and folder name) is in **English**. Domain terms get their English name in the glossary and that is the one that holds in code.
- The conversation with the user (answers, questions, decision options) is in pt-BR. A passage that will become a file comes out in English already in the response.

## README.md

- Project purpose.
- How to run (prerequisites, installation, commands).
- How to test.
- Summarized directory structure.
- License and contribution (if open).

## CHANGELOG.md

- Follow [Keep a Changelog](https://keepachangelog.com/).
- Sections: Added, Changed, Deprecated, Removed, Fixed, Security.
- Versions in descending order. The newest version at the top.
- Each entry must be understandable without reading the code.

```markdown
## [1.2.3] - 2026-09-29
### Added
- OAuth2 authentication support.

### Fixed
- Fixes Hikari pool connection leak.
```

## Versioning

- Use SemVer: MAJOR.MINOR.PATCH.
- MAJOR: incompatible changes.
- MINOR: compatible features.
- PATCH: fixes.
- Git tags: `v1.2.3`.

## ADRs

- Important architectural decisions go in `docs/adr/0001-decision-title.md`.
- Structure: context, decision, consequences.

## Commits

- Conventional Commits: `type(scope): description`.
- Types: feat, fix, docs, style, refactor, test, chore.
- Optional body for details; footer for breaking changes and issue references.

## Code comments

- Avoid unnecessary explanatory comments.
- Document public APIs (JavaDoc, GDScript docstrings).
- Explain the "why", not the "what".
