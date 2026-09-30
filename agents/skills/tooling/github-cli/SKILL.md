---
name: github-cli
version: "1.0"
description: Uses gh and git for branches, commits, PRs, releases and reviews following best practices. Use on branches, commits, PRs and releases.
triggers:
  - user
  - model
allowed-tools:
  - read
  - exec
---

# GitHub CLI Expert

## Before any operation

1. Check `git status`, current branch and remote.
2. Confirm `gh` is authenticated (`gh auth status`). If not, ask for login.
3. Never expose tokens in chat.

## Workflow

1. Branch per task: `git switch -c feature/description`.
2. Atomic commits with Conventional Commits.
3. Run local checks (tests, lint, build).
4. Create the PR: `gh pr create --title "type(scope): ..." --body "..."`.
5. Track: `gh pr checks`, `gh pr view`.
6. Merge only after approval/tests: `gh pr merge`.

## Releases

- Use SemVer: `gh release create v1.2.3 --generate-notes`.
- Update `CHANGELOG.md` first.

## Security

- Do not force-push shared branches without explicit authorization.
- Do not commit secrets, `.env` or tokens.
- Do not rewrite public history without confirmation.
