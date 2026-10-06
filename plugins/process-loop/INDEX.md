# process-loop/ — ai-kit process loop — orchestrated batches

## `skills/`

| Skill | Description |
|---|---|
| `loop-child-fix` | Apply a loop fix round from .loop/findings.json. Use when a PR has gates or verdict findings. Not for new issues (skill loop-child-implement). |
| `loop-child-implement` | Implement one loop issue in its worktree. Use when given an issue number and repo. Not for fix rounds (skill loop-child-fix). |
| `loop-orchestrate` | Run a review-loop batch as architect. Use when the owner says start, status or stop. Not for PR review (skill loop-review). |
| `loop-review` | Review one loop PR into a verdict JSON. Use when the waiter hands a review item. Not for merges (skill loop-orchestrate). |

## `templates/`

- `doc-batch-report.md`
- `doc-verdict.md`

Content for the loop tool (verdict schema, example config): `platforms/kits/review-loop/README.md`.

Manifests: `.devin-plugin/plugin.json` (Devin) · `.claude-plugin/plugin.json` (Claude) · `plugin.json` (Codex).
