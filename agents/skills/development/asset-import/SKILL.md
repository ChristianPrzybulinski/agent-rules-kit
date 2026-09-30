---
name: asset-import
version: "1.0"
description: Importa sprites, animações, tilesets e mapas para um projeto Godot 2D a partir de originais externos (acervo legado, Krita, Aseprite) de forma determinística, não destrutiva e rastreável — originais intocados, derivados com manifesto (origem, hash, dimensões, pivô, aliases), relatório de rejeitados para revisão humana. Usar ao trazer arte para o projeto ou ao reprocessar um lote. Não usar para desenhar/editar arte (skill krita).
argument-hint: "[lote: caminho dos originais | FEAT-xxx]"
triggers:
  - user
  - model
allowed-tools:
  - read
  - grep
  - glob
  - exec
---

# Asset Import

Quatro áreas, nunca misturadas: **originais** (read-only) → **normalizados** (formato/nome padronizados, sem interpretação) → **derivados** (transparência, atlas, recortes — decisões registradas) → **importados** (o que o Godot lê, `res://`). Tudo que sai de um estágio tem manifesto apontando para o estágio anterior.

## 1. Antes do lote

- Ler regra de binários do projeto (`agents/rules/git/git-lfs-and-binaries.md`, `.gitattributes`): o que vai para LFS, o que fica fora do repo.
- Ler `docs/legacy/` (ou equivalente) para lacunas já conhecidas do acervo: pares divergentes, membros ausentes, transparência não resolvida. Não assumir completude.
- Confirmar hash dos originais contra o manifesto de origem. Divergência → parar e reportar.

## 2. Manifesto (um por lote, formato estável — CSV ou JSON)

Colunas mínimas: `origem_path, origem_sha256, cast, numero, nome, aliases, largura, altura, pivo_x, pivo_y, formato_origem, derivado_path, derivado_sha256, transformacoes, status(ok|rejeitado|revisar), motivo`.

- Duplicatas por hash: um derivado, todos os aliases preservados na mesma linha.
- Pares que divergem (ex.: PNG≠BMP do mesmo membro): `revisar`, nunca escolher automaticamente.

## 3. Transformações permitidas sem revisão

- Renomear/organizar; converter formato sem perda; recortar por metadados existentes; montar atlas/`SpriteFrames` a partir de frames já identificados.

## Transformações que exigem decisão registrada (DEC ou nota no manifesto por lote)

- Remoção de cor-chave (transparência): **nunca global**; por lote, com cor e tolerância explícitas, preview antes/depois.
- Alterar pivô/registro, reescalar, reordenar frames, inferir direção/duração de animação.

## 4. Godot

- Import presets do projeto (filtro desligado para pixel art, `mipmaps` off) via `.import`/preset — não por sprite.
- Atlas/tileset gerados por script reproduzível (`tools/`), com o comando no manifesto.
- Não copiar o acervo inteiro para `res://`; só o lote da FEAT.

## 5. Relatório do lote

Template: `agents/templates/doc-recovery-report.md`. Inclui contagens (entrada, ok, rejeitado, revisar), previews (caminhos), e o que **não** foi verificado.

## Regras

- Executar o script duas vezes deve produzir bytes idênticos (determinismo) — verificar por hash.
- Nenhuma escrita em originais; se o script precisar de permissão de escrita lá, está errado.
- Procedência/licença de uso por lote no manifesto ou no relatório; ausente → `[BLOQUEIO]` para distribuição, não para desenvolvimento.
