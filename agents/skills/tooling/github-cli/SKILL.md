---
name: github-cli
version: "1.0"
description: Usa gh e git para branches, commits, PRs, releases e reviews seguindo boas práticas. Usar em branches, commits, PRs e releases.
triggers:
  - user
  - model
allowed-tools:
  - read
  - exec
---

# GitHub CLI Expert

## Antes de qualquer operação

1. Verifique `git status`, branch atual e remote.
2. Confirme que `gh` está autenticado (`gh auth status`). Se não, peça login.
3. Nunca exponha tokens no chat.

## Fluxo de trabalho

1. Branch por tarefa: `git switch -c feature/descricao`.
2. Commits atômicos com Conventional Commits.
3. Rode verificações locais (testes, lint, build).
4. Crie PR: `gh pr create --title "type(scope): ..." --body "..."`.
5. Acompanhe: `gh pr checks`, `gh pr view`.
6. Merge só após aprovação/testes: `gh pr merge`.

## Releases

- Use SemVer: `gh release create v1.2.3 --generate-notes`.
- Atualize `CHANGELOG.md` antes.

## Segurança

- Não force-push em branches compartilhadas sem autorização explícita.
- Não comite segredos, `.env` ou tokens.
- Não reescreva histórico público sem confirmação.
