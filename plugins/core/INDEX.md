# core/ — ai-kit core — always-on rules, session, review, GitHub and security

## `skills/`

| Skill | Description |
|---|---|
| `git` | Branch, commit, PR, `gh`, release and LFS policy. Use when creating a branch, commit, PR or release, or adding a large binary. Not for PR gates (skill review). |
| `parallelize` | Parallel planning for tool calls, long commands and [P] tasks. Use when work has independent steps. Not for product concurrency (skill testing). |
| `review` | Completion verdict, claim check and PR gates. Use when asking “is it done?”, preparing a PR or testing a claim. Not for fixing failures (skill sdd-implement). |
| `security` | Security design and CVE, secret and endpoint scans. Use when changing a trust boundary or preparing a sensitive PR or release. Not for verdicts (skill review). |
| `session` | Session start, closeout and handoff. Use when starting, switching topic, closing, handing off or a second human joins. Not for parallelism (skill parallelize). |

## `agents/`

- `reviewer.md`

## `hooks/`

- `hooks.json`

## `templates/`

- `doc-session-handoff.md`

## `evals/`

- `git-squash-body`
- `review-claimed-proof-not-rerun`
- `session-closeout-no-rerun`

`AGENTS.md`: the always-on global rules.

Manifests: `.devin-plugin/plugin.json` (Devin) · `.claude-plugin/plugin.json` (Claude) · `plugin.json` (Codex).
