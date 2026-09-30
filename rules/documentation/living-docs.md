---
description: Documentação viva — README, Javadoc/docstrings, CHANGELOG, specs e ADRs atualizados no mesmo PR da mudança; o que documentar e o que não. Carregar ao fechar uma tarefa ou revisar PR.
trigger: model_decision
---

# Documentação viva

Documento desatualizado é pior que ausente: o agente confia nele. Toda mudança de comportamento atualiza a doc **no mesmo PR**.

## Checklist de fechamento (Definition of Done documental)

| Mudou... | Atualize |
|---|---|
| comando de build/run/test | `README.md` do módulo + `AGENTS.md` do repo |
| API pública Java | Javadoc na classe/método público (o quê + invariantes; não repita a assinatura) |
| script GDScript exportado/autoload | docstring `##` acima de `class_name`, `@export`, sinais |
| comportamento visível ao usuário | `CHANGELOG.md` seção `Unreleased` |
| mensagem do contrato cliente↔servidor | doc do protocolo + exemplo + `protocol_version` se incompatível |
| decisão com trade-off | `docs/spec/decisions/DEC-xxx.md` (estado `proposta` até aprovação) |
| status de uma feature | frontmatter de `docs/spec/features/FEAT-xxx.md` |
| dívida assumida conscientemente | `docs/spec/debts/DEBT-xxx.md` com gatilho de pagamento |

## Javadoc / docstring

- Só em API pública e em invariantes não óbvias. Getter, `record`, override trivial → sem Javadoc.
- Conteúdo: propósito, pré/pós-condições, exceções lançadas, thread-safety quando relevante. Sem `@author`, sem data.
- Exemplo curto vale mais que parágrafo.

## README de módulo/projeto

Propósito (2 linhas) → pré-requisitos com versões → comandos (build, run, test) → estrutura (5-10 linhas) → onde está o resto (`docs/`). Sem tutorial de framework.

## CHANGELOG

Keep a Changelog. `## [Unreleased]` sempre presente; release move para `## [X.Y.Z] - data`. Escreva o impacto para quem usa, não o diff.

## Condição → ação

- PR pronto → rodar o checklist acima; item aplicável sem atualização → PR não está pronto.
- Doc contradiz código → código vence; corrija a doc no PR atual (ou abra `DEBT` se for grande).
- Explicação longa no chat sobre como algo funciona → candidata a `knowledge/` ou `docs/`; não deixe só na conversa.
