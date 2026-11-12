# core/ — ai-kit core — always-on rules, session, review, GitHub and security

## `skills/`

| Skill | Description |
|---|---|
| `branching-and-versioning` | Branch, commit, PR and release policy. Use when creating a branch, flag, commit, PR, SemVer release or tag. Not for `gh` commands (skill github-cli). |
| `collab-two-humans` | Condition → action rules for two people plus agents on one backlog. Use when a second human joins. Not for solo work. |
| `github-cli` | `gh` PR workflow. Use when writing a PR body, checking reviews, merging or publishing a release. Not for branch policy (skill branching-and-versioning). |
| `parallelize` | Parallel planning for tool calls, long commands and [P] tasks. Use when work has independent steps. Not for product concurrency (skill testing). |
| `review-gates` | No-model PR gates on a pull request — contract, scope, proof. Use when reviewing or merging a PR. Not for PR creation (skill github-cli). |
| `secure-development` | Security design for dependencies, auth, endpoints and sensitive data. Use when changing a trust boundary. Not for scanning changes (skill vuln-scan). |
| `session` | Session start, closeout review and handoff record. Use when starting, changing topic, closing or leaving pending work. Not for parallelism (skill parallelize). |
| `skeptic` | Adversarial check of a claim or proposed fix. Use when the user suggests a solution or a claim has no source yet. Not for bugs (skill investigate). |
| `tokens` | Response register for code, e-mail, reports, README and governed docs. Use when writing long answers or text for humans. Not for doc policy (skill update-docs). |
| `validate-implementation` | Completion verdict against a request or FEAT. Use when asking “is it done?” or preparing a PR. Not for fixing failures (skill sdd-implement). |
| `vuln-scan` | Scan for CVEs, secrets and changed endpoints. Use when preparing a sensitive PR, release or requested audit. Not for security design (skill secure-development). |

## `agents/`

- `reviewer.md`

## `hooks/`

- `hooks.json`

## `templates/`

- `doc-session-handoff.md`

## `evals/`

- `branching-squash-body`
- `session-closeout-no-rerun`
- `validate-implementation-claimed-proof-not-rerun`

`AGENTS.md`: the always-on global rules.

Manifests: `.devin-plugin/plugin.json` (Devin) · `.claude-plugin/plugin.json` (Claude) · `plugin.json` (Codex).
