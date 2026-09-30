---
description: Política de binários e Git LFS — o que vai para LFS, o que não entra no repo, arquivos gerados, preservação de originais. Carregar ao adicionar assets, exports, imagens, áudio ou arquivos grandes.
trigger: model_decision
---

# Binários e Git LFS

## Regras

- `.gitattributes` na raiz define LFS **antes** do primeiro binário entrar. Adicionar padrão depois exige `git lfs migrate` (reescreve histórico).
- Vai para LFS: `*.png *.jpg *.webp *.wav *.ogg *.mp3 *.ttf *.otf *.psd *.kra *.aseprite *.zip` e qualquer arquivo >1 MB.
- **Não entra no repo**: acervo bruto/legado (fica fora, com hash registrado), exports de build (`build/`, `*.exe`, `*.app`, `*.pck`), `.godot/`, `target/`, dumps de banco.
- Arquivo gerado por script determinístico (atlas, tileset, conversão) → **não** versionar; versionar o script + manifesto (origem, hash, parâmetros). Exceção: se gerar leva >5 min ou exige ferramenta ausente no CI — aí versiona em LFS com o manifesto.
- Godot: versionar `*.import`; nunca `.godot/`.

## Preservação de legado

- Originais são só-leitura, fora do repo, com `SHA256SUMS` versionado.
- Toda conversão escreve em área separada com `manifest.json` (origem, hash de entrada, hash de saída, ferramenta+versão, parâmetros).
- Nunca sobrescrever original; nunca "limpar" acervo automaticamente.

## Condição → ação

- Novo tipo de arquivo binário → adicionar ao `.gitattributes` **no mesmo commit** do primeiro arquivo.
- `git status` mostra binário >1 MB sem LFS → parar; corrigir antes de commitar.
- Clone novo → `git lfs install && git lfs pull`.
- Quota LFS do GitHub (Free/Pro: 10 GiB armazenamento + 10 GiB banda/mês — ver `knowledge/git/lfs-quotas-github.md`) → monitorar com `gh api repos/{owner}/{repo}` + `git lfs ls-files -s`; acervo grande fica fora do GitHub.
