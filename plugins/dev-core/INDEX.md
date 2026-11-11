# dev-core/ — ai-kit dev patterns — code-level standards

## `skills/`

| Skill | Description |
|---|---|
| `characterization-tests` | Tests that pin current behavior of legacy or ported code. Use when refactoring or rebalancing a rule with no spec. Not for new behavior (skill testing). |
| `code-standards` | Names, functions, comments, errors and the YAGNI ladder. Use when writing or reviewing code or adding a dependency. Not for test policy (skill testing). |
| `investigate` | Root-cause investigation with reproduction. Use when a bug, slow behavior or incident has no named cause. Not for implementing fixes (skill sdd-implement). |
| `testing` | Test policy and gates. Use when setting coverage/mutation gates or deciding what not to test. Not for legacy tests (skill characterization-tests). |
| `update-docs` | Project documentation closure. Use when updating README, CHANGELOG, Javadoc, ADR or release notes. Not for feature specs (skill sdd-specify). |
## `templates/`

- `doc-bug-report.md`
- `doc-load-test.md`
- `doc-recovery-report.md`


## `evals/`

- `investigate-no-fix-without-repro`
- `investigate-perf-needs-number`
- `investigate-report-is-hypothesis`
- `testing-correction-reruns-delta`
- `testing-docs-only-proof`
- `testing-empty-return-passes`
- `testing-honest-test-impractical`
- `testing-parity-gdscript-coverage`
- `testing-surviving-mutant-green-gate`
- `testing-unchanged-result-reused`
- `testing-workflow-is-not-docs`

Manifests: `.devin-plugin/plugin.json` (Devin) · `.claude-plugin/plugin.json` (Claude) · `plugin.json` (Codex).
