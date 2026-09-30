---
name: github-cli
version: "2.0"
description: Uses `gh` and git for branches, commits, PRs, releases and reviews — authentication, PR body with what/why/how-to-test, merge only after checks. Use when creating branches, commits, PRs or releases. Do not use for the branching/SemVer policy (skill branching-and-versioning) or LFS (skill git-lfs).
triggers:
  - user
  - model
allowed-tools:
  - read
  - grep
  - glob
  - exec
---

# GitHub CLI Expert

`gh` for PRs, issues, releases and status; `git` locally for commits, branches, stash and rebase.

## Before any operation

1. Check `git status`, current branch and remote.
2. Confirm `gh` is authenticated (`gh auth status`). If not, ask the user to run `gh auth login`.
3. Tokens come from `GH_TOKEN`/`GITHUB_TOKEN` env — never expose them in chat.

## Workflow

1. Branch per task: `git switch -c feature/description` (`fix/`, `docs/` likewise).
2. Atomic commits with Conventional Commits.
3. Run local checks (tests, lint, build) before merging.
4. Create the PR: `gh pr create --title "feat: add JWT authentication" --body "## Summary..."` — body: what changed, why, how to test; link issues with `Closes #123`.
5. Track: `gh pr checks`, `gh pr view`.
6. Merge only after approval/tests: `gh pr merge`.

## Releases

- SemVer: `gh release create v1.2.3 --generate-notes`.
- Update `CHANGELOG.md` first.

## Security

- Do not commit secrets, `.env` or tokens.
- Do not force-push shared branches without explicit user confirmation.
- Do not rewrite public history without authorization.
