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

Run `git status` and identify the branch/remote. Distinguish connectivity failures from authentication failures:

- DNS errors, timeouts, or `error connecting to api.github.com` do not establish invalid credentials. For authorized reads, use the GitHub connector when it supports the operation; otherwise request narrowly scoped sandbox escalation for the exact CLI command. Do not change persistent permissions.
- Check `gh auth status` through a working network path. Ask the user to run `gh auth login` only when the result establishes missing or invalid authentication. A permission or rate-limit error alone does not justify logging in again.
- Never print `GH_TOKEN` or `GITHUB_TOKEN`. Do not blindly retry mutations after an ambiguous failure; first check whether the operation took effect.

## 2. Create the PR

Run required local gates, then use `gh pr create`. The body states what changed, why, exact test commands/results and linked issues (`Closes #n`/`Refs: FEAT-nnn`). Do not use a generic generated body without evidence.

Then wait for the PR checks (`gh pr checks <n> --watch`) and add each check's name and conclusion to the PR. A failing check opens that report; never omit it. Local gates do not replace CI-only gates such as dependency or secret scans, so the PR is not done while a check is red.

## 3. Review and merge

- Inspect `gh pr checks`, `gh pr view` and review comments.
- Resolve findings and rerun affected gates before merge.
- Merge only after required approvals/checks, using the repository's squash policy.

## 4. Protect history

Never force-push or rewrite public history without explicit authorization. If an authorized feature-branch rebase requires it, use `git push --force-with-lease`, never plain `--force` and never on `main`.

## 5. Publish a release

After `VERSION` and CHANGELOG are ready under the branching/versioning policy, use `gh release create vX.Y.Z` with curated notes or the approved changelog excerpt; verify the resulting tag/release.

Done when: authentication is valid, the PR body contains evidence, every PR check is reported by name and passes, reviews pass, merge follows policy and any release matches its approved version/tag.
