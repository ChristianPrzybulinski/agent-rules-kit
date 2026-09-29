---
description: Detalhes de Clean Code (nomes, funções, classes, comentários, testes). Carregar ao escrever ou revisar código de produção; o resumo já está no AGENTS.md.
trigger: model_decision
---

# Clean Code

## Nomes

- Nomes de variáveis, funções, classes e métodos devem revelar intenção.
- Evite abreviações obscuras, prefixos desnecessários e números mágicos sem constante.

## Funções e métodos

- Curto: idealmente até 20 linhas; máximo recomendado 40.
- Fazem **uma única coisa** (Single Responsibility Principle).
- Máximo 3-4 parâmetros; para mais, use objetos/records/DTOs.
- Evite efeitos colaterais ocultos.

## Classes e módulos

- Coesão alta; acoplamento baixo.
- Abra para extensão, feche para modificação (OCP).
- Prefira composição sobre herança.
- Não exponha estado interno desnecessariamente.

## Controle e fluxo

- Evite aninhamento profundo (>3 níveis). Extraia funções ou use early returns.
- Trate erros de forma explícita, não com códigos de retorno especiais.
- Não ignore exceções/erros sem justificativa documentada.

## Comentários

- O código deve ser autoexplicativo.
- Comentários só para explicar o "porquê", não o "o quê".
- Não deixe código comentado morto no repositório.

## Testes

- Código sem testes é código que não funciona.
- Nomeie testes de forma descritiva: `deve_<comportamento>_quando_<condicao>`.
- Um assert por teste idealmente; máximo um conceito por teste.
