---
description: Política de testes — cobertura 100% no domínio, mutation testing, integração com caminho feliz e triste, o que não testar. Carregar ao criar/alterar testes ou configurar gates de build.
trigger: model_decision
---

# Testes

## Gates (falham o build)

| Escopo | Gate | Ferramenta |
|---|---|---|
| Módulo `domain` (regras de negócio) | 100% linha e branch | JaCoCo `check` no módulo |
| Módulo `domain` | mutation score ≥ 80% | PITest |
| Demais módulos | sem gate numérico; **um** check executável por lógica não trivial | — |

Cobertura de linha é necessária, não suficiente: 100% com asserts fracos passa. Por isso PITest no domínio.

## Fora do domínio: YAGNI vale para testes

- Lógica não trivial (branch, loop, parser, mapeamento com regra, adapter com tradução) → **um** teste pequeno que falha se a lógica quebrar. Não uma suíte por método, não fixtures "para depois".
- Trivial (getter, `record`, mapeamento 1:1, one-liner, wiring de framework) → não testa.
- Integração de adapter: o par feliz+triste é o mínimo **e** o suficiente na maioria dos casos.
- Quando em dúvida se é domínio: se envolve dinheiro, inventário, recompensa, batalha, autorização — é domínio; gate completo.

## Esperar condição, nunca tempo

- Proibido `Thread.sleep`/`await_timer`/`time.sleep` em teste para "dar tempo". Espere a condição observável (`Awaitility`, `CountDownLatch`, sinal do Godot, polling com timeout curto). Teste que precisa de `sleep` está testando timing, não comportamento — ou tem race real a investigar.
- Timeout explícito e mensagem que diz **qual** condição não ocorreu.

## Pirâmide

1. **Unitário** (domínio): sem Spring, sem I/O, sem mocks de entidade. Mock só de ports.
2. **Integração** (adapters): banco real via Testcontainers; HTTP real via `WebTestClient`/`MockMvc`. Sempre em pares: **caminho feliz + caminho triste** (entrada inválida, recurso ausente, conflito, timeout).
3. **Contrato** (fronteira cliente↔servidor): exemplos de mensagem versionados, validados nos dois lados.
4. **E2E/smoke**: poucos, na fatia vertical.

## Condição → ação

- Corrigir bug → teste que reproduz, falhando pela razão certa, **antes** da correção.
- Nova regra de negócio → tabela de casos (válido / limite / inválido) em `@ParameterizedTest`.
- Dinheiro, inventário, recompensa → teste de idempotência (mesma operação 2x = mesmo estado) e de concorrência (2 threads, 1 vence).
- Teste falhando → corrija código ou teste; nunca `@Disabled` para ficar verde.
- Teste lento (>1s unitário, >10s integração) → investigue; provável I/O onde não devia.

## Nomenclatura

`deve_<resultado>_quando_<condicao>()` ou `should_<result>_when_<condition>()` — consistente por projeto. Estrutura Given/When/Then explícita no corpo (comentários ou blocos). Gherkin/Cucumber só se não-devs lerem as specs.

## Não teste

- Getters/setters, `record`, construtores triviais.
- Framework (Spring já testa Spring).
- Implementação ("verifica que chamou X") em vez de comportamento.
