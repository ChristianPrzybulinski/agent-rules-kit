---
description: Higiene de sessão — planejar antes de executar, uma sessão = um resultado, detectar mistura de contexto e sessão longa, sugerir nível de modelo menor para tarefa simples, atualizar o kit no início. Carregar no início de toda sessão e quando o pedido muda de assunto.
trigger: model_decision
---

# Sessões

Sessão curta e focada custa menos tokens e erra menos. Estas regras existem para o agente **propor** a disciplina, não para travar o usuário: ele decide.

## Início

- Se `~/.ai-kit` existe: `~/.ai-kit/platforms/tools/refresh.sh --quiet` (sai em silêncio se nada mudou; layout novo → reinstala).
- Ler `AGENTS.md` do repo; identificar **o** resultado desta sessão em uma frase. Não conseguiu? pergunte antes de qualquer leitura ampla.

## Planejar antes de executar

- Tarefa com 3+ arquivos, cruza camada, ou pedido ambíguo → se a sessão **não** está em modo de planejamento, sugerir a troca em uma linha ("isto pede plano; troca para modo plan?") antes de tocar em arquivo. Tarefa de 1-2 arquivos e mecânica → executar direto.
- Plano aprovado → executar sem re-planejar a cada passo.

## Uma sessão, um resultado

- Um resultado = uma FEAT, um bug, uma decisão, um documento. Pedido de outro contexto no meio → **alertar e parar**: "isto é outro assunto; registro como follow-up e continuamos o atual, ou encerramos e abrimos nova sessão?" Nunca misturar em silêncio.
- Follow-ups vão para o registro de passagem (`session-handoff`), não para a memória do agente.

## Sessão longa

Sinais: releitura de arquivos já lidos, contexto resumido/comprimido, resultado original já entregue e novos pedidos chegando, mais de ~2h de trabalho. Ao notar um sinal → sugerir: `session-handoff` + nova sessão. Continuar só se o usuário disser.

## Nível do agente

- Tarefa simples (mecânica, 1-2 arquivos, sem decisão, sem investigação) → dizer em uma linha que um modelo/nível menor resolve, e seguir com o atual se o usuário não trocar.
- Tarefa com decisão de arquitetura, investigação ou risco → não sugerir rebaixar.

## Fim

- `session-handoff` se a sessão produziu algo ou deixou pendência.
- Working tree limpo ou listado como `[BLOQUEIO]`.
