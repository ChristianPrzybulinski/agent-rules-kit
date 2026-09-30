# Teste de carga — [cenário] — YYYY-MM-DD

FEAT/REQ: `REQ-NF-xxx`  ·  Servidor: `[repo @ commit]`  ·  Ferramenta: `[clientes sintéticos: cmd/script @ commit]`

## Hipótese

[HIPÓTESE] [ex.: 200 sessões simultâneas em 1 região mantêm p95 de resposta a `Move` < 100 ms]

## Ambiente

| Item | Valor |
|---|---|
| Hardware/VM | [CPU, RAM] |
| JVM | [versão, `-Xmx`, GC] |
| Banco | [versão, pool size] |
| Rede | [local | LAN | latência injetada N ms] |

## Cenário

- Perfil: [N clientes, rampa X/s, duração Y min, mix de mensagens %]
- Semente/fixtures: [`...`] (reproduzível)

## Métricas

| Métrica | Alvo | Medido | Fonte |
|---|---|---|---|
| p50/p95/p99 [msg] | | | [Micrometer/log] |
| erros/s | 0 | | |
| CPU / heap / GC pause | | | |
| conexões DB / lock wait | | | |
| fila de eventos (tamanho máx.) | | | |

## Resultado

- Veredicto: [FATO] hipótese confirmada / refutada em [ponto de quebra]
- Gargalo observado: [`arquivo/componente`] — evidência: [...]

## Não verificado / limitações

- [ex.: rede real, clientes reais, mix de mensagens inventado]
