---
name: github-cli
description: "`gh` PR workflow. Use when writing a PR body, checking reviews, merging or publishing a release. Not for branch policy (skill branching-and-versioning)."
triggers:
  - user
  - model
allowed-tools:
  - read
  - grep
  - glob
  - exec
---

# GitHub CLI

## 1. Check local and remote state

Run `git status`, identify the branch/remote and verify `gh auth status`. If authentication is missing, ask the user to run `gh auth login`; never print `GH_TOKEN` or `GITHUB_TOKEN`.

## 2. Create the PR

Run required local gates, then use `gh pr create`. The body states what changed, why, exact test commands/results and linked issues (`Closes #n`/`Refs: FEAT-nnn`). Do not use a generic generated body without evidence.

## 3. Review and merge

- Inspect `gh pr checks`, `gh pr view` and review comments.
- Resolve findings and rerun affected gates before merge.
- Merge only after required approvals/checks, using the repository's squash policy.

## 4. Protect history

Never force-push or rewrite public history without explicit authorization. If an authorized feature-branch rebase requires it, use `git push --force-with-lease`, never plain `--force` and never on `main`.

## 5. Publish a release

After `VERSION` and CHANGELOG are ready under the branching/versioning policy, use `gh release create vX.Y.Z` with curated notes or the approved changelog excerpt; verify the resulting tag/release.

Done when: authentication is valid, the PR body contains evidence, reviews/checks pass, merge follows policy and any release matches its approved version/tag.
