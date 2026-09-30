---
id: REQ-NF-000
title: "[Atributo de qualidade em 1 frase mensurável]"
type: non-functional
category: performance
priority: should
metric: "[o que medir, unidade]"
target: "[valor ou HIPÓTESE]"
measurement: "[como/onde medir]"
features: []
created: "YYYY-MM-DD"
---

# REQ-NF-000 — [Título]

## Enunciado

[Ex.: O servidor deve processar uma ação de batalha em ≤ 100 ms (p95) com 50 batalhas simultâneas.]

## Métrica e alvo

| Métrica | Alvo | Estado do alvo | Como medir |
|---|---|---|---|
| [p95 latência ação] | [100 ms] | `[HIPÓTESE]` até teste de carga | [ferramenta, cenário, ambiente] |

Alvo sem medição planejada não é requisito — é desejo. Marque `[HIPÓTESE]` e diga quando será medido.

## Racional

[Por quê esse valor. Fonte se houver.]

## Features afetadas

- `FEAT-000`
