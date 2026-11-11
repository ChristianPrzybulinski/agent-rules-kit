# quality-core/ — ai-kit quality — review and verification

## `skills/`

| Skill | Description |
|---|---|
| `skeptic` | Adversarial check of a claim or proposed fix. Use when the user suggests a solution or a claim has no source yet. Not for bugs (skill investigate). |
| `validate-implementation` | Completion verdict against a request or FEAT. Use when asking “is it done?” or preparing a PR. Not for fixing failures (skill sdd-implement). |
## `agents/`

- `reviewer.md`

## `evals/`

- `validate-implementation-claimed-proof-not-rerun`

Manifests: `.devin-plugin/plugin.json` (Devin) · `.claude-plugin/plugin.json` (Claude) · `plugin.json` (Codex).
