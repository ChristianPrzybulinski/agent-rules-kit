---
name: sdd-to-card
version: "1.0"
description: Etapa 9 do SDD — sincroniza uma FEAT com um card no GitHub (Issue + Project) via gh - cria a issue se não existir, atualiza título/corpo/labels/status a partir do frontmatter, grava o número no campo card da FEAT. Usar após specify (abrir) e após validate/merge (fechar).
argument-hint: "FEAT-nnn [--project <número>]"
triggers:
  - user
  - model
allowed-tools:
  - read
  - edit
  - exec
---

# SDD 9 — To Card (GitHub Issues + Projects)

Decisão do produto: GitHub Issues + Projects (não Trello). `gh` já autenticado; nunca imprimir token.

## Mapeamento

| FEAT (frontmatter) | GitHub |
|---|---|
| `id` + `title` | título da issue: `FEAT-nnn: <title>` |
| corpo (Problema, Escopo, Critérios) | corpo da issue (link para o arquivo no repo, não cópia integral) |
| `status` | label `status:<valor>` + coluna do Project (Status) |
| `requirements` | lista no corpo com links |
| `card` | número da issue (`#42`) |
| `flag` | label `flag` se não nulo |

## Etapas

1. Ler FEAT. `card: null` → criar:
   ```bash
   gh issue create --title "FEAT-nnn: <title>" --body-file <(gerar corpo) --label "feature,status:<status>"
   ```
   Gravar `card: <n>` no frontmatter e commitar `docs(spec): liga FEAT-nnn à issue #n`.
2. `card` existente → `gh issue edit <n> --title ... --body-file ... --add-label status:<novo> --remove-label status:<antigo>`.
3. Project (se `--project` ou campo `project` em `spec.md`): `gh project item-add <num> --owner <owner> --url <issue-url>`; atualizar campo Status via `gh project item-edit` (requer IDs — obter com `gh project field-list`). Se o Project não existir → perguntar antes de criar.
4. `status: entregue` → `gh issue close <n> --comment "Entregue em <PR>"`.
5. Labels `status:*` e `feature` ausentes no repo → criar com `gh label create` (uma vez).

## Critérios de conclusão

- `gh issue view <n>` reflete título, status e links da FEAT.
- FEAT tem `card` preenchido e commitado.

## Não faça

- Copiar a spec inteira para a issue (fonte de verdade é o arquivo).
- Criar issues para REQ/DEC/DEBT — só FEAT vira card. DEBT pode virar issue com label `debt` **se o usuário pedir**.
