---
name: update-docs
version: "2.0"
description: Updates README, CHANGELOG, ADRs and semantic versioning. Use when closing a visible change, editing docs or preparing a release. Do not use for spec artifacts — they follow the `spec-*` templates and schemas.
triggers:
  - user
  - model
allowed-tools:
  - read
  - grep
  - glob
  - write
  - edit
---

# Documentation Expert

Per-change checklist ("living docs"): `references/living-docs.md`.

## Language

- Written artifacts (README, CHANGELOG, spec, ADR/DEC, comment, commit, file and folder names) in **English**; the conversation with the user stays in pt-BR. A passage that will become a file comes out in English already in the response.

## Always

1. Keep `README.md` in sync with the project: purpose, prerequisites, install/run/test commands, summarized structure, license/contribution.
2. Update `CHANGELOG.md` (Keep a Changelog) on every relevant change — the entry must be understandable without reading the code.
3. Record architectural decisions in `docs/adr/XXXX-title.md`: context, decision, consequences.
4. Conventional Commits (`type(scope): description` — feat, fix, docs, style, refactor, test, chore; footer for breaking changes and issue references) and SemVer.

## CHANGELOG

- Format: `## [X.Y.Z] - YYYY-MM-DD`; versions in descending order, newest on top.
- Sections: Added, Changed, Deprecated, Removed, Fixed, Security.
- Each entry describes the impact for the user, not the code.

```markdown
## [1.2.3] - 2026-09-29
### Added
- OAuth2 authentication support.
```

## Versioning

- MAJOR: incompatible changes.
- MINOR: compatible features.
- PATCH: fixes.
- Git tags: `vX.Y.Z`.

## Comments and public API

- Comments explain the "why", not the "what"; no dead commented-out code.
- Public APIs get Javadoc/docstrings — purpose and invariants, not the signature restated.
