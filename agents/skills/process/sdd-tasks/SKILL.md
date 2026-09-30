---
name: sdd-tasks
version: "1.0"
description: Etapa 6 do SDD — quebra o plano de uma FEAT em tarefas pequenas, ordenadas por dependência, cada uma com critério de conclusão verificável e teste associado. Usar após plan; saída é a seção Tarefas na FEAT.
argument-hint: "FEAT-nnn"
triggers:
  - user
allowed-tools:
  - read
  - edit
---

# SDD 6 — Tasks

Pré-requisito: `status: planejada`.

## Regras de quebra

- Tarefa é **pequena**: ≈ 5-30 min de execução, ≤ 5 arquivos, um único comando/teste que prova a conclusão. Se a descrição precisa de "e também", são duas tarefas. Cada tarefa nomeia os caminhos exatos (não "os arquivos do módulo").
- Ordem: contrato/tipos → domínio + testes unitários → persistência + migração → adapters + integração → cliente → flag/docs. Testes andam **com** a tarefa, não em tarefa separada no fim.
- Cada tarefa: `T-nn` · título imperativo · arquivos previstos · critério de conclusão (comando ou teste que prova) · critérios de aceite cobertos (`CA-n`) · dependências (`T-mm`).
- Tarefas independentes marcadas `[P]` (paralelizáveis).
- Primeira tarefa de toda FEAT com regra de negócio: "escrever testes de domínio que falham" (Red).

## Formato (seção **Tarefas** da FEAT)

```markdown
| ID | Tarefa | Arquivos | Prova de conclusão | Cobre | Depende | Estado |
|---|---|---|---|---|---|---|
| T-01 | Definir mensagens MoveRequest/MoveResult no contrato | protocol/... | exemplo valida no schema | CA-1, CA-2 | — | todo |
| T-02 [P] | Testes de domínio de movimento (falhando) | server/domain/src/test/... | `./mvnw -pl domain test` vermelho pelo motivo certo | CA-1..3 | T-01 | todo |
```

Estados: `todo · doing · done · blocked`.

## Critérios de conclusão

- Todo critério de aceite aparece em ≥1 tarefa; toda tarefa cobre ≥1 critério (ou é infra explícita).
- Nenhuma tarefa "implementar o resto".
- `sdd-analyze` A8 passa.
