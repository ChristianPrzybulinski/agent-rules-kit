# templates/ — artifact skeletons

Scope: shape, not content. Every file created by the agent or the kit is born from a template here. The prefix says where the artifact lives.

| Prefix | Where the artifact lives | Templates |
|---|---|---|
| `spec-` | the **project**'s `docs/spec/` (validated by `platforms/ci/schemas/{spec,feature,requirement,decision,debt}.schema.json`) | `spec-index.md` (→ `docs/spec/spec.md`) · `spec-feature.md` · `spec-requirement-functional.md` · `spec-requirement-non-functional.md` · `spec-decision.md` · `spec-debt.md` |
| `doc-` | the project's `docs/` (sessions, incidents, reports, protocol) | `doc-session-handoff.md` · `doc-bug-report.md` · `doc-recovery-report.md` · `doc-load-test.md` · `doc-contract-message.md` · `doc-review-checklist.md` |
| `project-` | the project root | `project-agents-java-spring.md` · `project-agents-godot-2d.md` (→ the repo's `AGENTS.md`) |
| `kit-` | this kit | `kit-reference.md` · `kit-skill.md` · `kit-index.md` · `kit-readme.md` |

## Which to use when

| Creating… | Template | Then |
|---|---|---|
| feature, requirement, decision, debt | `spec-*` | `platforms/tools/check.sh --spec docs/spec` |
| session end | `doc-session-handoff.md` | `session-handoff` skill |
| investigated bug/incident | `doc-bug-report.md` | `investigate` skill |
| imported art batch | `doc-recovery-report.md` | `asset-import` skill |
| load test | `doc-load-test.md` | corresponding REQ-NF |
| contract message | `doc-contract-message.md` | `protocol-contract` skill |
| PR review | `doc-review-checklist.md` | — |
| new Java / Godot repo | `project-agents-*.md` | `sdd-constitution` |
| kit note, skill, index | `kit-*` | `platforms/tools/check.sh` |

Naming rule: `^(spec|doc|project|kit)-[a-z0-9-]+\.md$` — validated by CI. A new template enters this table in the same commit.
