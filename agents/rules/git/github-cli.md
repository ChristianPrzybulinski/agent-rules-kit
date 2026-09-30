---
description: Rules for using the GitHub CLI (gh) and Git/GitHub workflows. Load when creating branches, commits, PRs or releases.
trigger: model_decision
---

# GitHub CLI

## Preferred commands

- Use `gh` to create/list PRs, issues, releases and check status.
- Use `git` locally for commits, branches, stash and rebase.

## Workflow

1. Always check `git status` and the current branch before changing anything.
2. Create a branch per task: `feature/description`, `fix/description`, `docs/description`.
3. Atomic commits with Conventional Commits.
4. Open a PR via `gh pr create` with a clear title and description.
5. Before merging, run checks locally (tests, lint, build).

## PRs

```bash
gh pr create --title "feat: add JWT authentication" --body "## Summary..."
```

- Description must contain: what changed, why, how to test.
- Link issues with `Closes #123`.
- Use `gh pr view`, `gh pr checks`, `gh pr merge` after approval.

## Releases and versioning

- Use semantic versioning (SemVer).
- Create releases via `gh release create v1.2.3 --generate-notes`.
- Keep `CHANGELOG.md` up to date.

## Security

- Never commit secrets, tokens or `.env`.
- Do not force-push shared branches without explicit user confirmation.
- Do not rewrite public history without authorization.

## Authentication

- Use `gh auth login` and configure via `GH_TOKEN` / `GITHUB_TOKEN` (never expose in chat).
- If `gh` is not authenticated, ask the user to run `gh auth login`.
