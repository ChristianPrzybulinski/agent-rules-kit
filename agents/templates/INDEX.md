# templates/ — esqueletos de artefatos

Escopo: forma, não conteúdo. Todo arquivo criado pelo agente ou pelo kit nasce de um template daqui. Prefixo diz onde o artefato vive.

| Prefixo | Onde o artefato vive | Templates |
|---|---|---|
| `spec-` | `docs/spec/` do **projeto** (validados por `platforms/ci/schemas/{spec,feature,requirement,decision,debt}.schema.json`) | `spec-index.md` (→ `docs/spec/spec.md`) · `spec-feature.md` · `spec-requirement-functional.md` · `spec-requirement-non-functional.md` · `spec-decision.md` · `spec-debt.md` |
| `doc-` | `docs/` do projeto (sessions, incidents, reports, protocol) | `doc-session-handoff.md` · `doc-bug-report.md` · `doc-recovery-report.md` · `doc-load-test.md` · `doc-contract-message.md` · `doc-review-checklist.md` |
| `project-` | raiz do projeto | `project-agents-java-spring.md` · `project-agents-godot-2d.md` (→ `AGENTS.md` do repo) |
| `kit-` | este kit | `kit-rule.md` · `kit-knowledge.md` · `kit-skill.md` · `kit-index.md` · `kit-readme.md` |

## Quando usar qual

| Vai criar… | Template | Depois |
|---|---|---|
| feature, requisito, decisão, dívida | `spec-*` | `platforms/tools/check.sh --spec docs/spec` |
| fim de sessão | `doc-session-handoff.md` | skill `session-handoff` |
| bug/incidente investigado | `doc-bug-report.md` | skill `investigate` |
| lote de arte importado | `doc-recovery-report.md` | skill `asset-import` |
| teste de carga | `doc-load-test.md` | REQ-NF correspondente |
| mensagem do contrato | `doc-contract-message.md` | skill `protocol-contract` |
| revisão de PR | `doc-review-checklist.md` | — |
| novo repo Java / Godot | `project-agents-*.md` | `sdd-constitution` |
| regra, nota, skill, índice do kit | `kit-*` | `platforms/tools/check.sh` |

Regra de nome: `^(spec|doc|project|kit)-[a-z0-9-]+\.md$` — validada pelo CI. Template novo entra nesta tabela no mesmo commit.
