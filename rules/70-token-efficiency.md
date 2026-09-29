---
description: Detalhes de economia de tokens. Carregar quando a tarefa envolve muitos arquivos ou respostas longas; o resumo já está no AGENTS.md.
trigger: model_decision
---

# Economia de Tokens

## Antes de responder

- Entenda o mínimo necessário para resolver. Não resolva problemas que não foram perguntados.
- Leia apenas os arquivos relevantes. Não faça buscas amplas sem necessidade.

## Respostas

- Seja denso: uma frase bem escrita vale mais que um parágrafo.
- Use bullets e tabelas para economizar tokens em listas.
- Evite introduções como "Claro!", "Com certeza!", "Vamos lá!".
- Ao explicar código, foque no que mudou e por quê.

## Código

- Produza diffs ou snippets mínimos quando possível.
- Não reescreva arquivos inteiros se a alteração for local.
- Para múltiplas mudanças pequenas, agrupe por arquivo e seja direto.

## Planejamento

- Use TODOs internos para estruturar, mas não exponha passos desnecessários ao usuário.
- Antes de implementar grande funcionalidade, valide a abordagem com o usuário em poucas frases.

## Evite repetição

- Não repita instruções gerais (essas regras já estão no contexto).
- Não reescreva o que o usuário já disse.
