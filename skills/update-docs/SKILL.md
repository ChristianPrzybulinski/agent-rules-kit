---
name: update-docs
description: Project documentation closure. Use when updating README, CHANGELOG, Javadoc, ADR or release notes. Not for feature specs (skill sdd-specify).
triggers:
  - user
  - model
allowed-tools:
  - read
  - grep
  - glob
  - edit
---

# Update Documentation

Use `references/living-docs.md` as the closure checklist. Written artifacts are English and updated in the same PR as behavior.

## 1. Classify the visible change

- Build/run/test command changed → update README and repository AGENTS instructions.
- User-visible behavior changed → add a Keep a Changelog `Unreleased` entry.
- Public API changed → add concise Javadoc/docstring for purpose and invariants.
- Rejected alternative/trade-off → create `DEC-nnn` proposed until approved.
- Conscious debt → create `DEBT-nnn` with a payment trigger.
- Feature progress → update FEAT status/history/frontmatter.

## 2. Update narrative docs

Keep README purpose, versioned prerequisites, exact build/run/test commands, short structure and pointers current. Remove stale commands rather than preserving historical alternatives.

## 3. Update code-facing docs

Document public Java APIs and exported GDScript/signals only when behavior or non-obvious invariants require it. Do not document getters, records, trivial overrides or signatures verbatim.

## 4. Maintain CHANGELOG and release notes

Write user impact under `## [Unreleased]` using Added/Changed/Deprecated/Removed/Fixed/Security. On release, move entries to `## [X.Y.Z] - YYYY-MM-DD`; release notes and tag must match VERSION/SemVer policy.

## 5. Verify closure

Search for the old command/name/version, resolve relative links and run the documentation/project checks. If documentation contradicts code, observed code wins and the docs change now.

Done when: each applicable checklist item is updated in the same PR, public/decision/debt/feature records are current, links pass and release notes match VERSION.
