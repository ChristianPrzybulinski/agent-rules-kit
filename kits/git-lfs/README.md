# kit git-lfs

`.gitattributes` pronto para projetos com arte/binário (Godot 2D em particular).

## Uso

1. Copie `.gitattributes` para a raiz do repo **antes** do primeiro binário entrar — adicionar depois exige `git lfs migrate` (reescreve histórico).
2. `git lfs install` (uma vez por máquina). Clone novo: `git lfs install && git lfs pull`.
3. Novo tipo binário → adicione o padrão **no mesmo commit** do primeiro arquivo.

Regras completas: `rules/git/git-lfs-and-binaries.md`. Quotas do GitHub: `knowledge/git/lfs-quotas-github.md`.
