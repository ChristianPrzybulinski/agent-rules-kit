---
description: Detalhes de Clean Code (nomes, funções, classes, comentários, testes). Carregar ao escrever ou revisar código de produção; o resumo já está no AGENTS.md.
trigger: model_decision
---

# Clean Code

## Nomes

- **Inglês, sempre** — identificadores, pacotes, arquivos, pastas, Javadoc, comentários, mensagens de log e de erro. Mistura de idioma no código é bug de revisão.
- Curto, objetivo, literal: `balance`, `findByPlayer`, `BattleTurn`. O nome diz o que é, não como foi feito nem quem o usa.
- Proibido: abreviação não universal (`usr`, `qtd`, `mgr`), sufixo decorativo (`Manager`, `Helper`, `Util`, `Data`, `Info`, `Impl` sem segunda implementação), prefixo de tipo (`strName`, `IRepository`), número mágico sem constante.
- Booleano lê como pergunta (`isActive`, `hasStock`); coleção no plural (`items`); método com verbo (`apply`, `find`, `reserve`); classe com substantivo.
- Um conceito, um nome: não alterne `player`/`user`/`character` para a mesma coisa. Glossário do projeto (`docs/spec/spec.md`) é a fonte.

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
