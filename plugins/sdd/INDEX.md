# sdd/ — ai-kit SDD — architecture, contracts and the spec-driven pipeline

## `skills/`

| Skill | Description |
|---|---|
| `architecture` | Layers, ports, DDD blocks and pattern choice. Use when placing a class, defining an aggregate or picking a pattern. Not for contracts (skill protocol-contract). |
| `grilling` | Grill the user relentlessly about a plan, decision, or idea. Use when the user wants to stress-test their thinking, or uses any 'grill' trigger phrases. |
| `protocol-contract` | Client↔server contracts. Use when adding a message or field, changing a payload or fixing a client/server mismatch. Not for transport choice (skill sdd-plan). |
| `sdd-check` | SDD step 3 — mechanical spec check and quality checklist. Use when a clarified FEAT needs gap checks before planning. Not for ambiguity (skill sdd-clarify). |
| `sdd-clarify` | SDD step 2 — resolve ambiguous FEAT criteria. Use when a FEAT has open questions or vague terms. Not for gap checks (skill sdd-check). |
| `sdd-constitution` | SDD step 0 — project constitution and spec index. Use when starting a project or changing principles. Not for one feature (skill sdd-specify). |
| `sdd-implement` | SDD step 6 — task-by-task Red-Green-Refactor delivery. Use when a FEAT has ordered tasks. Not for completion verdicts (skill review). |
| `sdd-journey` | Journey layer — J-NN steps cite REQ ids, tasks and tests. Use when writing a user-visible flow. Not for FEATs (skill sdd-specify). |
| `sdd-plan` | SDD step 4 — technical FEAT plan and decisions. Use when clarification and check are complete. Not for task breakdown (skill sdd-tasks). |
| `sdd-specify` | SDD step 1 — feature and requirement specification. Use when a described feature needs FEAT/REQ criteria. Not for open questions (skill sdd-clarify). |
| `sdd-spike` | Prototype lane for game feel. Use when movement, camera, battle feedback or UI must be felt on screen before a FEAT exists. Not for specs (skill sdd-specify). |
| `sdd-tasks` | SDD step 5 — dependency-ordered implementation tasks. Use when a FEAT has an approved technical plan. Not for execution (skill sdd-implement). |
| `sdd-to-card` | SDD step 8 — one GitHub issue per task row plus the FEAT card. Use when cutting issues or closing a FEAT. Not for PR operations (skill git). |

## `rules/`

- `spec.md`

## `agents/`

- `researcher.md`

## `templates/`

- `doc-spike-report.md`
- `spec-debt.md`
- `spec-decision.md`
- `spec-feature.md`
- `spec-index.md`
- `spec-journey.md`
- `spec-requirement-functional.md`
- `spec-requirement-non-functional.md`

## `evals/`

- `protocol-contract-required-field-bumps-version`

Manifests: `.devin-plugin/plugin.json` (Devin) · `.claude-plugin/plugin.json` (Claude) · `plugin.json` (Codex).
