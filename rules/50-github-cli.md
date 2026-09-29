---
description: Regras para uso do GitHub CLI (gh) e fluxos Git/GitHub.
trigger: model_decision
---

# GitHub CLI

## Comandos preferidos

- Use `gh` para criar/listar PRs, issues, releases e verificar status.
- Use `git` localmente para commits, branches, stash e rebase.

## Fluxo de trabalho

1. Sempre verifique `git status` e a branch atual antes de alterar.
2. Crie branch por tarefa: `feature/descricao`, `fix/descricao`, `docs/descricao`.
3. Commits atômicos com Conventional Commits.
4. Abra PR via `gh pr create` com título e descrição claros.
5. Antes de merge, rode verificações localmente (testes, lint, build).

## PRs

```bash
gh pr create --title "feat: adiciona autenticação JWT" --body "## Sumário..."
```

- Descrição deve conter: o que mudou, por quê, como testar.
- Relacione issues com `Closes #123`.
- Use `gh pr view`, `gh pr checks`, `gh pr merge` após aprovação.

## Releases e versionamento

- Use versionamento semântico (SemVer).
- Crie releases via `gh release create v1.2.3 --generate-notes`.
- Mantenha `CHANGELOG.md` atualizado.

## Segurança

- Nunca comite segredos, tokens ou `.env`.
- Não force-push em branches compartilhadas sem confirmação explícita do usuário.
- Não reescreva histórico público sem autorização.

## Autenticação

- Use `gh auth login` e configuração via `GH_TOKEN` / `GITHUB_TOKEN` (nunca exponha no chat).
- Se `gh` não estiver autenticado, peça ao usuário para rodar `gh auth login`.
