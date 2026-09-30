---
name: characterization-tests
version: "1.0"
description: Cria testes de caracterização que fixam o comportamento ATUAL de código legado ou portado (fórmulas, tabelas, RNG, arredondamento) antes de refatorar, migrar ou rebalancear. Usar antes de tocar em regra cujo comportamento correto não está especificado. Não usar para validar regra nova (aí é teste normal com spec).
argument-hint: "[classe/método legado | fluxo: dano, evolução, encontro...]"
triggers:
  - user
  - model
allowed-tools:
  - read
  - grep
  - glob
  - exec
---

# Characterization Tests

Objetivo: transformar "o código faz X" de `[HIPÓTESE]` em `[FATO]` reproduzível, para que qualquer mudança futura seja **deliberada** e visível num diff de teste.

## 1. Delimitar a unidade

- Uma regra por vez: entrada → saída pura (dano, chance de captura, XP, preço). Se a regra depende de I/O, isolar primeiro por seam mínimo (interface para RNG, relógio, repositório) — sem mudar comportamento.
- Registrar a fonte: arquivo:linha do código atual **e**, se houver, o original de onde foi portado (ex.: script Lingo). Só `[FATO]` para o que foi lido.

## 2. Gerar casos

- Limites: zero, negativo, máximo, overflow de tipo, vazio, nulo.
- Arredondamento e divisão inteira: casos onde truncar vs arredondar divergem.
- RNG: injetar semente/sequência fixa; caracterizar a distribuição por amostragem só se a fórmula não for legível.
- Tabelas (níveis, tipos, preços): fixture pequena em arquivo (`src/test/resources/characterization/<regra>.csv`), não constantes inline.
- Casos surpreendentes (bug aparente) entram **como estão**, com comentário `// CARACTERIZAÇÃO: comportamento atual, não validado como correto` e um `DEBT-xxx` se for relevante.

## 3. Escrever

- Nome: `<Regra>CharacterizationTest`; método: `given<entrada>_returns<saidaAtual>`.
- Parametrizado (JUnit `@ParameterizedTest` + `@CsvFileSource`) quando >5 casos.
- Executar e confirmar verde na versão atual: `./mvnw -q -pl <módulo> test -Dtest=<Classe>`. Saída literal no relatório.

## 4. Comparar com o original (quando existir)

- Se o original é executável (raro): mesma fixture nos dois; divergência é achado, vai para tabela `esperado-legado / atual-Java / decisão`.
- Se não é executável: leitura lado a lado, fórmula transcrita no teste como comentário, divergência marcada `[HIPÓTESE]` até decisão.

## 5. Fechar

- FEAT/DEC que motivou: linkar a classe de teste em "Relações".
- Divergência que precisa de decisão de produto → `DEC-xxx` `proposta` com as duas opções e impacto.
- Só depois disso o refactor/rebalanceamento começa — e cada mudança intencional atualiza o caso com justificativa no commit.

## Regras

- Não "corrigir" o comportamento durante a caracterização.
- Não caracterizar via mock do próprio código sob teste.
- Percentuais de cobertura/portabilidade herdados de relatórios antigos não substituem esta etapa.
