---
name: branching-and-versioning
description: Branch, commit, PR and release policy. Use when creating a branch, flag, commit, PR, SemVer release or tag. Not for `gh` commands (skill github-cli).
triggers:
  - user
  - model
allowed-tools:
  - read
  - grep
  - glob
  - exec
---

# Branching and Versioning

## 1. Start from releasable main

`main` is the only long-lived branch and stays green. Update it, then create `feature/FEAT-nnn-name` (`fix/`, `docs/`, `chore/` for non-features). Do not create develop or release branches. `spike/<topic>` is the only exception: it is time-boxed (skill sdd-spike), never merged to `main`, and deleted after its report.

## 2. Keep incomplete work safe

- Merge incomplete behavior only behind a flag defaulting off and recorded in the FEAT.
- A flag continuously on for more than 30 days creates a `DEBT-nnn` removal item.
- Security or integrity rules never hide behind a flag.

## 3. Commit atomically

Use `<type>(<scope>): <imperative description>` with `Refs: FEAT-nnn`, `Closes #n` or `BREAKING CHANGE:` as applicable. One commit represents one coherent change; no AI attribution in the title (a co-author footer only if the project requires it).

## 4. Integrate without rewriting history

Except for `spike/` branches, rebase the feature onto current `main`, run gates, then use a squash PR so one feature becomes one main commit. Ask before any force-push and use `--force-with-lease` only on the feature branch; never rewrite public `main` history.

## 5. Select versions

- SemVer: breaking change → MAJOR, compatible feature → MINOR, fix → PATCH; tag `vX.Y.Z` on `main`.
- Pre-release uses `-alpha.N` until releasable.
- Client/server `protocol_version` is a separate integer: compatible optional fields keep it; incompatible changes increment it and require an explicit compatibility window.

Done when: the change has a short-lived branch, atomic Conventional Commits, green squash PR, safe flag state and justified app/protocol versions.
