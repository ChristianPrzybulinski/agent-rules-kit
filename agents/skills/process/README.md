# SDD — Spec-Driven Development

Processo adaptado do [github/spec-kit](https://github.com/github/spec-kit) (skills `speckit-*`), sem o CLI `specify` (exige Python 3.11+/uv). Aqui as etapas são skills do kit, e os artefatos vivem **no repositório do projeto**, em `docs/spec/` — nunca no kit.

## Fluxo

```text
constitution (1x por projeto)  →  AGENTS.md do repo + docs/spec/spec.md
        │
   specify  →  clarify  →  analyze  →  audit  →  plan  →  tasks  →  implement  →  validate  →  to-card
   FEAT-xxx    perguntas    coerência   checklist  plano    lista     código        veredicto    issue GH
   REQ-*       resolvidas   spec↔req    de gaps    técnico  ordenada  + testes      PRONTO?      + status
```

Repita `implement → validate` até PRONTO. `to-card` pode rodar logo após `specify` (abre o card) e de novo após `validate` (fecha).

| Etapa | Skill | Entrada | Saída | Origem no spec-kit |
|---|---|---|---|---|
| 0 | `sdd-constitution` | pedido do produto, stack | `AGENTS.md`, `docs/spec/spec.md` | `constitution` |
| 1 | `sdd-specify` | descrição da funcionalidade | `features/FEAT-xxx.md` (status `proposta`), `requirements/**/REQ-*.md` | `specify` |
| 2 | `sdd-clarify` | FEAT | perguntas → respostas incorporadas; status `clarificada` | `clarify` |
| 3 | `sdd-analyze` | FEAT + REQs + DECs | relatório de contradições/lacunas/órfãos | `analyze` |
| 4 | `sdd-audit` | FEAT | checklist de qualidade da spec (testável? completa? segura?) | `checklist` |
| 5 | `sdd-plan` | FEAT clarificada | seção *Plano* na FEAT (módulos, contrato, migração, flag, testes); `DEC-xxx` se decisão; status `planejada` | `plan` |
| 6 | `sdd-tasks` | plano | seção *Tarefas* ordenadas, cada uma com critério verificável | `tasks` |
| 7 | `sdd-implement` | tarefas | código + testes + docs, uma tarefa por vez; status `em-implementação` | `implement` |
| 8 | `core/validate-implementation` | FEAT | veredicto PRONTO/PARCIAL/NÃO PRONTO; status `validada` | `converge` |
| 9 | `sdd-to-card` | FEAT | issue no GitHub (Projects) sincronizada com status | — (adição) |

## Identificadores

| Sigla | Onde | Exemplo |
|---|---|---|
| `FEAT-nnn` | `docs/spec/features/` | `FEAT-003-login.md` |
| `REQ-F-nnn` | `docs/spec/requirements/functional/` | `REQ-F-012-senha-argon2.md` |
| `REQ-NF-nnn` | `docs/spec/requirements/non-functional/` | `REQ-NF-004-latencia-batalha.md` |
| `DEC-nnn` | `docs/spec/decisions/` | `DEC-002-websocket-vs-tcp.md` |
| `DEBT-nnn` | `docs/spec/debts/` | `DEBT-001-flag-login-antiga.md` |

Numeração sequencial por tipo, nunca reutilizada. Nome do arquivo: `SIGLA-nnn-slug.md`. Frontmatter validado por `platforms/ci/schemas/*.schema.json` (CI via `platforms/kits/github/workflows/spec-lint.yml`).

## Status de feature

`proposta → clarificada → planejada → em-implementação → validada → entregue` (+ `cancelada`). Só avança; regressão exige nota em *Histórico*. `entregue` = merged na `main` com flag ligada (ou sem flag).

## Classificação obrigatória de afirmações (em toda spec/decisão)

`[FATO]` verificado com fonte · `[DECISÃO]` aprovada pelo produto · `[PROPOSTA]` técnica aguardando aprovação · `[HIPÓTESE]` a validar, com como validar · `[BLOQUEIO]` dependência externa.

## Layout no projeto

```text
docs/spec/
├── spec.md                      # capa: visão, escopo, glossário, índice de FEAT/REQ/DEC/DEBT
├── features/FEAT-nnn-slug.md
├── requirements/
│   ├── functional/REQ-F-nnn-slug.md
│   └── non-functional/REQ-NF-nnn-slug.md
├── decisions/DEC-nnn-slug.md
└── debts/DEBT-nnn-slug.md
```

Templates em `agents/templates/`. Bootstrap: `platforms/kits/sdd/init-spec.sh <repo>` copia a estrutura vazia.
