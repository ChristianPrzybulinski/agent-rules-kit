---
name: session-handoff
version: "1.0"
description: Registra a passagem entre sessões de trabalho — o que foi feito com evidência, o que ficou pendente, decisões tomadas/abertas e a primeira tarefa concreta da próxima sessão. Usar ao encerrar uma sessão longa, antes de trocar de agente/ferramenta, ou quando o contexto vai ser perdido.
argument-hint: "[FEAT-xxx | tema da sessão]"
triggers:
  - user
  - model
allowed-tools:
  - read
  - grep
  - glob
  - exec
---

# Session Handoff

Uma nova sessão deve conseguir continuar sem esta conversa. O registro é curto, factual e aponta para artefatos — não repete conteúdo que já está em spec/DEC/commit.

## 1. Coletar (não de memória)

- `git status --short` e `git log --oneline <base>..HEAD` em cada repo tocado: o que foi commitado, o que ficou sujo.
- Specs com `status`/`updated` alterados nesta sessão (`grep -l "updated: <hoje>" docs/spec -r`).
- Comandos de verificação rodados e a saída literal resumida (OK / FALHOU + trecho).
- Perguntas feitas ao usuário e respostas obtidas.

## 2. Escrever

Template: `agents/templates/doc-session-handoff.md`. Destino no projeto: `docs/sessions/YYYY-MM-DD-<tema>.md` (criar pasta se não existir; se o projeto definir outro local no `AGENTS.md`, use-o).

Cada item classificado: `[FATO]` (observado), `[DECISÃO]` (aprovada, com DEC), `[PROPOSTA]`, `[HIPÓTESE]`, `[BLOQUEIO]`.

## 3. Primeira tarefa da próxima sessão

Exatamente uma, executável sem perguntas: comando ou arquivo + critério de pronto. Se depende de decisão do usuário, a tarefa é "obter decisão X" com as opções listadas.

## Regras

- Não afirmar "testado"/"funciona" sem comando + saída no registro.
- Não copiar trechos longos de spec; linkar.
- Working tree sujo é `[BLOQUEIO]` explícito, com os arquivos listados.
- Registro entra no mesmo commit/PR que fecha a sessão; se nada foi commitado, o registro é o único commit.
