---
name: sdd-analyze
version: "1.0"
description: Etapa 3 do SDD — análise de consistência entre FEAT, REQs, DECs, plano e tarefas - contradições, lacunas, requisitos órfãos, critérios sem tarefa, tarefas sem critério. Somente leitura; produz relatório. Usar após clarify e após plan/tasks.
argument-hint: "FEAT-nnn | all"
triggers:
  - user
  - model
allowed-tools:
  - read
  - glob
  - grep
---

# SDD 3 — Analyze

Somente leitura. Não edita specs; o relatório vai para o chat (e opcionalmente `docs/spec/reports/analyze-YYYYMMDD.md` se o usuário pedir).

## Verificações

| # | Checagem | Severidade |
|---|---|---|
| A1 | REQ referenciado na FEAT existe como arquivo; arquivo REQ é referenciado por ≥1 FEAT | alta |
| A2 | Critério de aceite contradiz outro critério ou um REQ (ex.: "sem login" vs REQ auth) | crítica |
| A3 | FEAT depende de FEAT com status inferior (planejar sobre o que não foi clarificado) | alta |
| A4 | Termo usado não está no glossário de `spec.md` | baixa |
| A5 | Quantificador vago sem número nem `[HIPÓTESE]` | média |
| A6 | Afirmação sem classificação `[FATO]/[DECISÃO]/[PROPOSTA]/[HIPÓTESE]/[BLOQUEIO]` | média |
| A7 | (se há plano) decisão técnica no plano sem `DEC` quando há alternativa rejeitada | média |
| A8 | (se há tarefas) critério de aceite sem tarefa que o cubra; tarefa sem critério | alta |
| A9 | Plano viola regra do kit/repo (ex.: Redis como fonte de verdade; Gradle; framework no domínio) | crítica |
| A10 | Frontmatter inválido contra `schemas/` | alta |

## Relatório

```
Escopo: FEAT-nnn | all
| # | Severidade | Onde (arquivo:linha) | Problema | Sugestão |
Resumo: N críticas, M altas, ...
Bloqueia avançar para <próxima etapa>? SIM (críticas/altas) | NÃO
```

Crítica ou alta → não avance para `plan`/`implement` até resolver (via `clarify` ou edição da spec).
