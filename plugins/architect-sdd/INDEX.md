# architect-sdd/ — ai-kit SDD — spec-driven development pipeline

## `skills/`

| Skill | Description |
|---|---|
| `sdd-analyze` | SDD step 3 — cross-artifact consistency report. Use when FEAT/REQ/DEC/plan/tasks need gap checks. Not for spec quality (skill sdd-audit). |
| `sdd-audit` | SDD step 4 — spec quality checklist. Use when a clarified FEAT needs testability, security and completeness checks. Not for consistency (skill sdd-analyze). |
| `sdd-clarify` | SDD step 2 — resolve ambiguous FEAT criteria. Use when a FEAT has open questions or vague terms. Not for quality auditing (skill sdd-audit). |
| `sdd-constitution` | SDD step 0 — project constitution and spec index. Use when starting a project or changing principles. Not for one feature (skill sdd-specify). |
| `sdd-implement` | SDD step 7 — task-by-task Red-Green-Refactor delivery. Use when a FEAT has ordered tasks. Not for completion verdicts (skill validate-implementation). |
| `sdd-journey` | Journey layer — J-NN steps cite REQ ids, tasks and tests. Use when writing a user-visible flow. Not for FEATs (skill sdd-specify). |
| `sdd-plan` | SDD step 5 — technical FEAT plan and decisions. Use when clarification and audit are complete. Not for task breakdown (skill sdd-tasks). |
| `sdd-specify` | SDD step 1 — feature and requirement specification. Use when a described feature needs FEAT/REQ criteria. Not for open questions (skill sdd-clarify). |
| `sdd-tasks` | SDD step 6 — dependency-ordered implementation tasks. Use when a FEAT has an approved technical plan. Not for execution (skill sdd-implement). |
| `sdd-to-card` | SDD step 9 — sync a FEAT to GitHub Issues/Projects. Use when opening, updating or closing its card. Not for PR operations (skill github-cli). |
## `rules/`

- `spec.md`

## `agents/`

- `researcher.md`

## `templates/`

- `spec-debt.md`
- `spec-decision.md`
- `spec-feature.md`
- `spec-index.md`
- `spec-journey.md`
- `spec-requirement-functional.md`
- `spec-requirement-non-functional.md`


Manifests: `.devin-plugin/plugin.json` (Devin) · `.claude-plugin/plugin.json` (Claude) · `plugin.json` (Codex).
