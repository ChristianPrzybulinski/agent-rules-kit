# dev-core/ — ai-kit dev patterns — code-level standards

## `skills/`

| Skill | Description |
|---|---|
| `characterization-tests` | Tests that pin current behavior of legacy or ported code. Use when refactoring or rebalancing a rule with no spec. Not for new behavior (skill testing). |
| `clean-code` | Code rules for names, functions and comments. Use when naming, editing functions, writing comments or reviewing code. Not for test policy (skill testing). |
| `frontend-design` | Guidance for distinctive, intentional visual design when building new UI or reshaping an existing one. Helps with aesthetic direction, typography, and making choices that don't read as templated defaults. |
| `investigate` | Root-cause investigation with reproduction. Use when a bug, slow behavior or incident has no named cause. Not for implementing fixes (skill sdd-implement). |
| `simplicity` | YAGNI ladder for the smallest change. Use when choosing a dependency, reviewing an oversized PR or adding an abstraction. Not for test gates (skill testing). |
| `testing` | Test policy and gates. Use when setting coverage/mutation gates or deciding what not to test. Not for legacy tests (skill characterization-tests). |
| `update-docs` | Project documentation closure. Use when updating README, CHANGELOG, Javadoc, ADR or release notes. Not for feature specs (skill sdd-specify). |
## `templates/`

- `doc-bug-report.md`
- `doc-load-test.md`
- `doc-recovery-report.md`


Manifests: `.devin-plugin/plugin.json` (Devin) · `.claude-plugin/plugin.json` (Claude) · `plugin.json` (Codex).
