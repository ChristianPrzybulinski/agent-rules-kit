---
name: validate-implementation
version: "1.0"
description: Valida se uma implementação está realmente pronta — confronta o que foi entregue com a spec/feature (FEAT-xxx) ou com o pedido, roda os gates do projeto, verifica docs e emite veredicto PRONTO / PARCIAL / NÃO PRONTO com evidências. Usar antes de abrir PR, ao fechar tarefa, ou quando alguém afirma "está feito".
argument-hint: "[FEAT-xxx | caminho da spec | descrição do que deveria estar pronto]"
triggers:
  - user
  - model
allowed-tools:
  - read
  - grep
  - glob
  - exec
---

# Validate Implementation

"Feito" exige observação. Esta skill produz a observação. Não corrige nada: só mede e reporta. Correções voltam ao fluxo normal (ou `sdd/implement`).

## 1. Fixar o alvo

- Argumento é `FEAT-xxx` → ler `docs/spec/features/FEAT-xxx.md`; critérios de aceite e requisitos ligados (`REQ-*`) são o alvo.
- Argumento é caminho/descrição → extrair critérios verificáveis; se não houver nenhum, parar e pedir 1-3 critérios.
- Listar cada critério como linha da tabela final **antes** de verificar.

## 2. Verificar o que existe (não o que foi dito)

- `git diff <base>...HEAD --stat` e `git log`: o que realmente mudou. Arquivos citados no relatório mas ausentes no diff → marcar.
- Para cada critério: localizar o código que o implementa (`grep`), o teste que o prova, e a doc que o registra.
- Critério sem teste → não conta como atendido.

## 3. Rodar os gates do projeto

Leia `AGENTS.md`/README do repo para os comandos canônicos. Padrão do kit:

| Stack | Comando |
|---|---|
| Java/Maven | `./mvnw -q spotless:check verify` (inclui JaCoCo, PITest, Dependency-Check conforme POM) |
| Godot | `godot --path . --headless --quit` + runner de testes do projeto |
| Docs/spec | `scripts/check.sh` do kit ou lint de spec do projeto |

Saída literal do que falhou vai no relatório. Não resuma "alguns testes falharam".

## 4. Checklist de fechamento (de `rules/documentation/living-docs.md`)

CHANGELOG `Unreleased` · README se comando mudou · Javadoc/docstring em API pública nova · status da `FEAT` atualizado · `DEC`/`DEBT` criados se houve decisão/dívida · feature flag registrada se incompleto.

## 5. Veredicto

```
Alvo: FEAT-xxx — <título>
Veredicto: PRONTO | PARCIAL | NÃO PRONTO
Gates: <comando> → OK | FALHOU (<trecho literal>)
| Critério | Código | Teste | Doc | Status |
|---|---|---|---|---|
| ... | path:linha | path | path | ✓ / ✗ / parcial |
Não verificado: <o que não foi possível medir e por quê>
Próximo passo: <a menor ação que muda o veredicto>
```

## Regras

- PRONTO só com todos os critérios ✓ e gates OK. Um ✗ → PARCIAL. Gate falhando → NÃO PRONTO.
- Não aceite "testado manualmente" sem passo reproduzível.
- Se a spec estiver ambígua a ponto de impedir julgar um critério → reportar como lacuna da spec (não do código) e sugerir `sdd/clarify`.
