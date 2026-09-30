---
name: sdd-clarify
version: "1.0"
description: Etapa 2 do SDD — resolve os [NEEDS CLARIFICATION] de uma FEAT com perguntas objetivas (2-4 opções cada) ao produto, incorpora as respostas na spec e muda status para clarificada. Usar quando a FEAT tem perguntas abertas ou critérios ambíguos.
argument-hint: "FEAT-nnn"
triggers:
  - user
allowed-tools:
  - read
  - edit
  - ask_user_question
---

# SDD 2 — Clarify

## Etapas

1. Ler a FEAT e os REQs ligados. Coletar: marcadores `[NEEDS CLARIFICATION]`, critérios sem caminho triste, termos fora do glossário, quantificadores vagos ("rápido", "muitos", "seguro").
2. Priorizar: perguntas que mudam escopo ou arquitetura primeiro. Máximo **5 por rodada**; se sobrar, segunda rodada.
3. Cada pergunta: contexto em 1 linha + 2-4 opções com consequência de cada + recomendação marcada. Uma única chamada de `ask_user_question` por rodada.
4. Incorporar resposta **no lugar certo** (critério, escopo, requisito), não em seção "respostas". Registrar em *Histórico*: `YYYY-MM-DD clarify: <pergunta> → <resposta>`.
5. Resposta que é decisão técnica → não incorporar aqui; anotar para `sdd-plan`/`DEC`.
6. Zero marcadores restantes → `status: clarificada`.

## Critérios de conclusão

- Nenhum `[NEEDS CLARIFICATION]`; nenhum quantificador vago sem número ou sem `[HIPÓTESE]` com método de medição.
- Glossário de `spec.md` atualizado com termos novos.

## Não faça

- Responder você mesmo a pergunta de produto "para não incomodar". Decisão reversível e técnica → decida e registre `[PROPOSTA]`; decisão de produto/custo/risco → pergunte.
