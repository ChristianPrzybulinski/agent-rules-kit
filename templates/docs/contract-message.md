# [NomeDaMensagem] — [comando | evento | resposta | erro]

Direção: [C→S | S→C | ambos]  ·  Desde `protocol_version`: [x.y]  ·  FEAT: `FEAT-xxx`

## Propósito

[Uma frase: o que o emissor quer que aconteça / o que o receptor precisa saber.]

## Campos

| Campo | Tipo | Obrig. | Limites | Validado por | Notas |
|---|---|---|---|---|---|
| `[campo]` | [string/int/uuid/enum] | sim/não | [tamanho, faixa, regex] | servidor / cliente (UX) | |

Envelope comum (id, correlação, sequência, timestamp): ver `protocol/README.md`.

## Semântica

- Idempotência: [chave de dedupe | não se aplica (só leitura)]
- Ordem: [por sessão | por entidade `[x]`]; fora de ordem → [descartar | reordenar até N | erro `[CODIGO]`]
- Frequência máxima: [N/s por sessão]; excedente → [erro `RATE_LIMITED` | descarte silencioso]
- Tamanho máximo: [bytes]

## Respostas e erros

| Código | Quando | Cliente deve |
|---|---|---|
| `[OK_xxx]` | | |
| `[ERR_xxx]` | | |

## Exemplos (fixtures em `protocol/examples/[nome]/`)

- `valid-01.json` — [caso feliz]
- `invalid-01.json` — [campo ausente] → `[ERR_xxx]`
- `invalid-02.json` — [limite excedido] → `[ERR_xxx]`

## Legado relacionado

- [FATO | HIPÓTESE] [assunto/handler legado, arquivo:linha] — divergências: [PROPOSTA] [...]

## Compatibilidade

- Mudança: [minor | major] — motivo: [...]
- Janela de coexistência: [versões suportadas simultaneamente | corte em `vX`]
