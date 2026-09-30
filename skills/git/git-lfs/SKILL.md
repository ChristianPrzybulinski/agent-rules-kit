---
name: git-lfs
version: "1.0"
description: Configura e audita Git LFS num repositório — .gitattributes por tipo/tamanho, migração de binários já commitados, verificação de quota e de arquivos que escaparam do LFS. Usar ao iniciar repo com assets, ao adicionar novo tipo binário, ou quando `git status` mostra binário grande.
argument-hint: "[init | audit | migrate <padrão>]"
triggers:
  - user
  - model
allowed-tools:
  - read
  - exec
---

# Git LFS

Política em `rules/git/git-lfs-and-binaries.md`. Template de `.gitattributes` em `kits/git-lfs/`.

## init (repo novo ou sem LFS)

1. `git lfs install --local` (não altera config global).
2. Copiar `kits/git-lfs/.gitattributes` para a raiz; ajustar padrões ao projeto (Godot: manter `*.import` fora do LFS).
3. Commitar `.gitattributes` **antes** de qualquer binário: `git add .gitattributes && git commit -m "chore: configura Git LFS"`.
4. Verificar: `git lfs track` lista os padrões.

## audit

```bash
git lfs ls-files -s | sort -k3 -h | tail        # maiores em LFS
git lfs status                                   # pendentes
git ls-files -z | xargs -0 -I{} sh -c 'test $(stat -f%z "{}") -gt 1048576 && echo "{}"' \
  | while read f; do git check-attr filter "$f" | grep -q lfs || echo "FORA DO LFS: $f"; done
```
Arquivos >1 MB fora do LFS → listar com tamanho. Quota (GitHub Free/Pro: 10 GiB armazenamento + 10 GiB banda/mês; fonte em `knowledge/git/lfs-quotas-github.md`): `git lfs ls-files -s` somado; >70% → alertar.

## migrate (binário já commitado sem LFS)

Reescreve histórico. **Perguntar antes** se o repo tem remote com outros clones.
```bash
git lfs migrate info --everything --include="*.png,*.wav"     # prévia
git lfs migrate import --everything --include="*.png,*.wav"   # executa
git push --force-with-lease origin main                      # só com autorização explícita
```

## Veredicto

```
LFS: instalado | não instalado
.gitattributes: OK | ausente | incompleto (faltam: ...)
Fora do LFS (>1MB): <lista ou nenhum>
Uso estimado: N MB (quota GitHub Free 10 GiB)
Próximo passo: ...
```
