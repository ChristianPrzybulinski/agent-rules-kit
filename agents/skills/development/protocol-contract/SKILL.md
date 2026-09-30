---
name: protocol-contract
version: "1.0"
description: Cria ou evolui uma mensagem do contrato cliente↔servidor (comando, evento, resposta, erro) com versionamento, exemplos testáveis e regras de compatibilidade. Usar ao adicionar/alterar campo, criar mensagem nova, ou ao encontrar cliente e servidor discordando sobre um payload. Não usar para decidir transporte/serialização (isso é DEC).
argument-hint: "[nome-da-mensagem | FEAT-xxx que precisa de mensagem nova]"
triggers:
  - user
  - model
allowed-tools:
  - read
  - grep
  - glob
  - exec
---

# Protocol Contract

O contrato vive num único lugar (no projeto, tipicamente `protocol/`); cliente e servidor consomem por versão. Esta skill muda o contrato, nunca os consumidores diretamente.

## 1. Localizar a fonte de verdade

- Ler `protocol/README.md` (ou o que `AGENTS.md` indicar): transporte, serialização, `protocol_version` atual, convenção de nomes, envelope comum (id, correlação, sequência, timestamp).
- Se não existir DEC aprovada para transporte/serialização → parar; abrir `DEC-xxx` como `proposta` e reportar. Não escolher por conta própria.

## 2. Classificar a mudança

| Mudança | `protocol_version` | Compatibilidade |
|---|---|---|
| Campo opcional novo; mensagem nova | minor | cliente antigo ignora |
| Campo obrigatório novo; tipo/semântica alterada; remoção | major | quebra — exige janela de coexistência ou corte planejado |
| Correção de doc/exemplo sem mudar bytes | nenhuma | — |

Major → precisa de DEC (mesmo curta) antes de seguir.

## 3. Especificar a mensagem

Template: `agents/templates/doc-contract-message.md`. Obrigatório por mensagem:

- direção (C→S, S→C, ambos), tipo (comando / evento / resposta / erro);
- campos com tipo, obrigatoriedade, limites (tamanho, faixa, frequência);
- quem valida o quê (servidor valida tudo que altera estado; cliente só pré-valida UX);
- idempotência: chave de deduplicação para comandos com efeito (inventário, economia, recompensa);
- ordem: sequência por sessão ou por entidade; o que acontece fora de ordem;
- erros possíveis com código estável (não texto);
- **exemplo válido e ≥1 inválido**, em arquivos separados sob `protocol/examples/`, para virarem fixtures de teste de contrato nos dois lados.

## 4. Legado como referência, não como molde

Se existe protocolo antigo: registrar em "Legado relacionado" o assunto/handler equivalente com `[FATO]` só se lido no código. Não copiar delimitadores, nomes obscuros ou campos sem função conhecida. Divergência de comportamento em relação ao legado → `[PROPOSTA]` explícita, nunca silenciosa.

## 5. Fechar

- `protocol/CHANGELOG.md` (ou seção) com a versão e a mudança.
- FEAT que motivou a mensagem: linkar a mensagem em "Relações".
- Exemplos passam num validador de schema se o projeto tiver (rodar; saída no relatório).

## Regras

- Nenhum campo "reservado para o futuro".
- Toda mensagem com efeito em estado tem resposta ou erro definido — sem fire-and-forget para comandos.
- Tamanho máximo e frequência máxima são parte do contrato, não detalhe do servidor.
