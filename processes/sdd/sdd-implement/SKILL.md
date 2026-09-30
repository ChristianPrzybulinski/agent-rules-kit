---
name: sdd-implement
version: "1.0"
description: Etapa 7 do SDD — executa as tarefas de uma FEAT uma a uma (Red→Green→Refactor), em branch feature/FEAT-nnn, atualizando estado das tarefas, docs e CHANGELOG; para em bloqueio e não inventa. Usar após tasks.
argument-hint: "FEAT-nnn [T-nn]"
triggers:
  - user
allowed-tools:
  - read
  - glob
  - grep
  - edit
  - write
  - exec
---

# SDD 7 — Implement

Pré-requisito: seção *Tarefas* existe. Regras do kit e `AGENTS.md` do repo valem integralmente.

## Etapas

1. Branch: `git switch -c feature/FEAT-nnn-slug` a partir de `main` atualizada (se ainda não existir). `status: em-implementação`.
2. Para cada tarefa em ordem (ou a `T-nn` indicada):
   1. Marcar `doing`. Ler os arquivos reais que vai tocar.
   2. Teste primeiro quando há comportamento: escrever/rodar → deve falhar pelo motivo certo. Não falhou? a tarefa não foi entendida — pare e reveja.
   3. Implementar o mínimo para verde. Refatorar com testes verdes.
   4. Rodar a *prova de conclusão* da tarefa literalmente; colar saída resumida no *Histórico*.
   5. Commit atômico: `feat(escopo): <tarefa>` + `Refs: FEAT-nnn`.
   6. Marcar `done`.
3. Bloqueio (dependência ausente, decisão de produto, regra violada) → `blocked` + motivo na FEAT; **não** contorne. Siga para tarefa independente `[P]` se houver; senão reporte.
4. Ao terminar todas: checklist de `rules/documentation/living-docs.md` (CHANGELOG `Unreleased`, README, Javadoc/docstring, flag registrada). Rodar gates completos (`./mvnw spotless:check verify`, `godot --headless --quit`, etc.).
5. Chamar `core/validate-implementation FEAT-nnn`. PARCIAL/NÃO PRONTO → voltar ao passo 2 com as tarefas que faltam.
6. PRONTO → `gh pr create` (título Conventional Commit; corpo com critérios ✓, comandos rodados, `Refs: FEAT-nnn`). Status muda para `validada` só após PR aberto com gates verdes; `entregue` após merge.

## Não faça

- Implementar fora do escopo da FEAT ("já que estou aqui"). Anote como follow-up.
- Desabilitar teste, baixar gate de cobertura, suprimir CVE sem justificativa.
- Afirmar que testou sem saída de comando registrada.
