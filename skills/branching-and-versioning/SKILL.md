---
name: branching-and-versioning
version: "1.0"
description: Trunk-based with main + feature/*, feature flags with expiry, Conventional Commits, SemVer and a separate protocol version. Use when creating a branch, committing, opening a PR, publishing a release or changing the contract. Do not use for `gh` command mechanics (skill github-cli).
triggers:
  - user
  - model
allowed-tools:
  - read
  - grep
  - glob
---

# Branches, commits and versioning

## Branches (trunk-based)

- `main` is the only long-lived branch; always green and releasable.
- Work → `feature/FEAT-001-short-name` (or `fix/`, `chore/`, `docs/`). Short-lived: days, not weeks.
- Merge via squash PR (1 feature = 1 commit on `main`) after green CI. No `develop`, no `release/*`.
- Rebase the feature onto `main` before the PR; never force-push `main`.

## Feature flags

- Incomplete functionality enters `main` **off** behind a flag (`app.features.<name>=false`).
- Flag recorded in `docs/spec/features/FEAT-xxx.md` (`flag` field).
- Flag 100% on for >30 days → open a `DEBT-xxx` to remove the flag and dead code.
- A flag never controls a security or integrity rule (those are always active).

## Conventional Commits

`<type>(<scope>): <imperative description>` — types: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`, `perf`, `build`, `ci`.
Footer: `Refs: FEAT-001` / `Closes #12` / `BREAKING CHANGE: ...`.
No AI attribution in the title; co-author in the footer if the project requires it.

## SemVer

- `MAJOR.MINOR.PATCH`. MAJOR = breaks compatibility; MINOR = compatible feature; PATCH = fix.
- Tag `vX.Y.Z` on `main`; `gh release create vX.Y.Z --notes-file <CHANGELOG excerpt>`.
- Version derived from commits (`feat` → MINOR, `fix` → PATCH, `BREAKING CHANGE` → MAJOR). No "manual bump by feel".
- Pre-release: `vX.Y.Z-alpha.N` until the vertical slice is playable.

## Protocol version (client↔server)

- Monotonic integer `protocol_version`, independent of app versions.
- Compatible change (new optional field) → same version. Incompatible → increment and the server accepts N and N-1 for one cycle.
- Handshake declares version; incompatible → explicit error with the required minimum version.

## Condition → action

- Start a task → `git switch -c feature/FEAT-xxx-name` from an updated `main`.
- Open a PR → Conventional Commit title; body: what, why, how tested, `Refs: FEAT-xxx`.
- Change a contract message → decide compatible/incompatible **before** coding; update `protocol_version` and the protocol CHANGELOG.
