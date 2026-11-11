# core/ — ai-kit core — always-on rules, session discipline and kit-authoring

## `skills/`

| Skill | Description |
|---|---|
| `collab-two-humans` | Condition → action rules for two people plus agents on one backlog. Use when a second human joins. Not for solo work. |
| `parallelize` | Parallel planning for tool calls, long commands and [P] tasks. Use when work has independent steps. Not for product concurrency (skill testing). |
| `session` | Session start, closeout review and handoff record. Use when starting, changing topic, closing or leaving pending work. Not for parallelism (skill parallelize). |
| `tokens` | Response register for code, e-mail, reports, README and governed docs. Use when writing long answers or text for humans. Not for doc policy (skill update-docs). |
## `agents/`


## `hooks/`

- `hooks.json`

## `templates/`

- `doc-session-handoff.md`
- `kit-index.md`
- `kit-readme.md`
- `kit-reference.md`
- `kit-skill.md`


## `evals/`

- `session-closeout-no-rerun`
- `session-closeout-points-to-pr`
- `session-closeout-simplification-proposal`
- `session-handoff-without-record`
- `session-worktree-cleanup`
- `tokens-bulk-log-summary`
- `tokens-human-register-no-cliches`
- `tokens-technical-register`

Manifests: `.devin-plugin/plugin.json` (Devin) · `.claude-plugin/plugin.json` (Claude) · `plugin.json` (Codex).
