# infra-github/ — ai-kit GitHub — SCM and delivery

## `skills/`

| Skill | Description |
|---|---|
| `branching-and-versioning` | Branch, commit, PR and release policy. Use when creating a branch, flag, commit, PR, SemVer release or tag. Not for `gh` commands (skill github-cli). |
| `github-cli` | `gh` PR workflow. Use when writing a PR body, checking reviews, merging or publishing a release. Not for branch policy (skill branching-and-versioning). |
| `review-gates` | No-model PR gates on a pull request — contract, scope, proof. Use when reviewing or merging a PR. Not for PR creation (skill github-cli). |

## `evals/`

- `github-cli-network-fallback`
- `github-cli-authentication-evidence`
- `github-cli-ambiguous-mutation`
- `branching-incomplete-behind-flag`
- `branching-no-develop-branch`
- `branching-squash-body`

Manifests: `.devin-plugin/plugin.json` (Devin) · `.claude-plugin/plugin.json` (Claude) · `plugin.json` (Codex).
