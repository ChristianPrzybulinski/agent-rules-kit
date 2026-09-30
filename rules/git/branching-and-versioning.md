---
description: Trunk-based com main + feature/*, feature flags com expiração, Conventional Commits, SemVer e versão de protocolo separada. Carregar ao criar branch, commitar, abrir PR, publicar release ou mudar contrato.
trigger: model_decision
---

# Branches, commits e versão

## Branches (trunk-based)

- `main` é a única branch longa; sempre verde e liberável.
- Trabalho → `feature/FEAT-001-nome-curto` (ou `fix/`, `chore/`, `docs/`). Vida curta: dias, não semanas.
- Merge via PR com squash (1 feature = 1 commit na `main`) após CI verde. Sem `develop`, sem `release/*`.
- Rebase da feature sobre `main` antes do PR; nunca force-push na `main`.

## Feature flags

- Funcionalidade incompleta entra na `main` **desligada** por flag (`app.features.<nome>=false`).
- Flag registrada em `docs/spec/features/FEAT-xxx.md` (campo `flag`).
- Flag 100% ligada há >30 dias → abrir `DEBT-xxx` para remover flag e código morto.
- Flag nunca controla regra de segurança ou integridade (essas são sempre ativas).

## Conventional Commits

`<tipo>(<escopo>): <descrição no imperativo>` — tipos: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`, `perf`, `build`, `ci`.
Footer: `Refs: FEAT-001` / `Closes #12` / `BREAKING CHANGE: ...`.
Sem atribuição a IA no título; co-author no footer se o projeto exigir.

## SemVer

- `MAJOR.MINOR.PATCH`. MAJOR = quebra compatibilidade; MINOR = feature compatível; PATCH = correção.
- Tag `vX.Y.Z` na `main`; `gh release create vX.Y.Z --notes-file <trecho do CHANGELOG>`.
- Versão gerada a partir dos commits (`feat` → MINOR, `fix` → PATCH, `BREAKING CHANGE` → MAJOR). Sem "bump manual por sentimento".
- Pré-release: `vX.Y.Z-alpha.N` até a fatia vertical estar jogável.

## Versão de protocolo (cliente↔servidor)

- Inteiro monotônico `protocol_version`, independente da versão dos apps.
- Mudança compatível (campo opcional novo) → mesma versão. Incompatível → incrementa e servidor aceita N e N-1 por um ciclo.
- Handshake declara versão; incompatível → erro explícito com versão mínima exigida.

## Condição → ação

- Começar tarefa → `git switch -c feature/FEAT-xxx-nome` a partir de `main` atualizada.
- Abrir PR → título Conventional Commit; corpo: o quê, porquê, como testou, `Refs: FEAT-xxx`.
- Mudar mensagem do contrato → decidir compatível/incompatível **antes** de codar; atualizar `protocol_version` e CHANGELOG do protocolo.
