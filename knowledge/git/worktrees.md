# Git worktrees

Verificado: 2026-09-30. Fonte: https://git-scm.com/docs/git-worktree

`git worktree` permite múltiplos diretórios de trabalho ligados ao mesmo repositório, cada um num branch diferente.

## Comandos

```bash
git worktree add ../projeto-fix feature/fix-x   # cria worktree (branch nova ou existente)
git worktree list                               # lista worktrees e seus HEADs
git worktree remove ../projeto-fix              # remove (exige árvore limpa; --force apaga)
git worktree prune                              # limpa metadados de worktrees já apagados do disco
```

## Quando usar

- Trabalho paralelo em 2 branches sem `stash`: hotfix em `main` enquanto uma feature continua aberta em outro diretório.
- Rodar testes/builds lentos de uma branch enquanto se edita outra.
- Revisar o checkout exato de uma tag/commit (`--detach`) sem tocar a árvore principal.

## Armadilhas

- A **mesma branch não pode estar checkada em dois worktrees** (impedido; use `--detach` ou outra branch).
- No worktree, `.git` é um **arquivo** apontando para `.git/worktrees/<nome>` do repo principal — ferramentas que assumem diretório `.git` podem falhar.
- Hooks ficam em `.git/hooks` do repo principal — **compartilhados** por todos os worktrees.
- Dois diretórios abertos: IDEs podem indexar os dois (uso de memória/CPU dobra); commits e staging são isolados, mas o histórico é o mesmo.
- Submódulos precisam de `git submodule update` por worktree.

Nota: ideia absorvida de obra/superpowers `using-git-worktrees` (MIT).
