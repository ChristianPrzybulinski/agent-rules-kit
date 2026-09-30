---
name: update-docs
version: "1.0"
description: Updates README, CHANGELOG, ADRs and semantic versioning. Use when closing a visible change or preparing a release.
triggers:
  - user
  - model
allowed-tools:
  - read
  - write
  - edit
---

# Documentation Expert

## Always

1. Keep `README.md` in sync with the project state.
2. Update `CHANGELOG.md` (Keep a Changelog) on every relevant change.
3. Record architectural decisions in `docs/adr/XXXX-title.md`.
4. Use Conventional Commits and SemVer.

## CHANGELOG

- Format: `## [X.Y.Z] - YYYY-MM-DD`
- Sections: Added, Changed, Deprecated, Removed, Fixed, Security.
- Each entry describes the impact for the user, not the code.

## README

- Purpose, installation, usage, tests, structure, license/contribution.

## ADR

1. Context
2. Decision
3. Consequences

## Versioning

- MAJOR: breaking changes.
- MINOR: compatible features.
- PATCH: fixes.
- Git tags: `vX.Y.Z`.
