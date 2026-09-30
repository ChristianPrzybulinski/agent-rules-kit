---
name: investigate
version: "1.0"
description: Investiga bug, regressão, problema de desempenho ou incidente até a causa raiz nomeada, com reprodução antes de qualquer correção. Usar quando algo "não funciona", está lento, ou falhou em produção/CI. Não usar para implementar a correção (volta ao fluxo normal com teste que falha primeiro).
argument-hint: "[descrição do sintoma | link do log/issue]"
triggers:
  - user
  - model
allowed-tools:
  - read
  - grep
  - glob
  - exec
---

# Investigate

Sintoma não é causa. Esta skill termina quando existe reprodução determinística e uma causa nomeada no código — ou quando fica claro o que falta para chegar lá.

## 1. Fixar o sintoma

- O que foi observado, onde (ambiente, versão/commit, plataforma), quando, com que frequência.
- O que era esperado, e por quê (spec, teste, doc, ou só expectativa do usuário — dizer qual).
- Relato de terceiro (issue, chat, memória) é `[HIPÓTESE]` até reproduzir.

## 2. Reproduzir

- Menor caminho que dispara o sintoma: teste automatizado > script > passos manuais numerados.
- Não conseguiu reproduzir → não "corrigir por intuição". Registrar tentativas e o que falta (dado, ambiente, acesso).
- Desempenho: medir antes (número + ferramenta + comando), não "parece lento".

## 3. Estreitar

- Bissecção quando houver commit bom conhecido (`git bisect`).
- Ler o caminho de código de fato executado (logs, breakpoints, `print` temporário), não o que "deveria" executar.
- Listar hipóteses concorrentes e procurar primeiro a evidência que **refuta** cada uma.
- Uma hipótese só vira causa quando explica todo o sintoma e a evidência mostra aquele trecho executando no cenário.

## 4. Relatar

Template: `templates/docs/bug-report.md` (sintoma, reprodução, causa, evidência, impacto, correção proposta, teste que deve passar a existir). Destino: issue do projeto ou `docs/incidents/` conforme `AGENTS.md`.

Incidente com dados/dinheiro/inventário afetados → seção de impacto com contagem verificada por consulta, não estimativa.

## Regras

- Corrigir só depois de um teste que falha pela razão certa (`rules/development/testing.md`).
- Remover instrumentação temporária antes de commitar; se ficar, é log estruturado deliberado.
- Causa "condição de corrida" ou "cache" exige demonstração (teste concorrente ou trace), não plausibilidade.
- Não fechar com "não reproduzido" sem listar o que foi tentado.
