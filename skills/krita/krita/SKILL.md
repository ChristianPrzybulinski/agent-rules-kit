---
name: krita
version: "1.0"
description: Krita para pixel art e retoque de sprites — configuração de documento (tamanho, sem antialias, paleta indexada), exportar PNG para Godot preservando transparência, spritesheets, e o que automatizar por script em vez de GUI. Usar ao preparar/corrigir arte 2D ou definir fluxo de exportação.
argument-hint: "[setup | export | spritesheet | automate]"
triggers:
  - user
allowed-tools:
  - read
  - exec
---

# Krita

Ferramenta **humana**; o agente orienta configuração e prepara scripts de lote fora do Krita quando possível (Python/Pillow ou ImageMagick — verificar instalação antes; não instalar sem autorização). Aseprite não está instalado (`[FATO]` nesta máquina); Krita cobre o essencial.

## setup (documento pixel art)

- Novo documento: dimensões exatas do sprite (ex.: 32×32, 64×64); 8 bits RGBA; 72 dpi (irrelevante para jogo).
- Pincel: `Pixel Art` preset (Krita ≥5) — sem antialias, opacidade 100%, tamanho 1 px.
- Ver → Grade: 1 px; Encaixar na grade ligado. Zoom em múltiplos inteiros.
- Paleta: importar `.gpl`/`.kpl` do projeto (`content/palettes/`); trabalhar só com cores da paleta (Docker "Paleta").
- Camadas: uma por parte animável (corpo, sombra, efeito); sombras em camada separada facilitam variantes.

## export (para Godot)

- Arquivo → Exportar → PNG: **desmarcar** "Achatar imagem" só se camadas forem exportadas separadas; **marcar** "Salvar canal alfa"; compressão indiferente (Godot reimporta).
- Não redimensionar no Krita para "aumentar pixel"; Godot faz o scale inteiro no viewport.
- Nome: `<entidade>_<animação>_<direção>_<frame>.png` (`player_walk_down_00.png`). Snake_case, sem espaço/acentos.
- Destino: `assets/` (fonte) → importado para `res://resources/sprites/`; Godot: filtro `Nearest` (ver `templates/projects/godot-2d/AGENTS.md`).

## spritesheet

- Krita não gera spritesheet nativamente bem; exportar frames e montar com script (`kits/godot/scripts/make_spritesheet.py` — Pillow) para determinismo e manifesto (`frames`, `size`, `pivot`).
- Godot lê frames via `SpriteFrames` ou `AtlasTexture`; documentar `hframes/vframes`.

## automate

- Tarefas repetitivas (recolorir paleta, recortar, redimensionar lote, remover cor de fundo **por arquivo verificado**) → script fora do Krita, com `manifest.json` de entrada/saída/hash (ver `rules/git/git-lfs-and-binaries.md`).
- Nunca remover "a cor X de todos os sprites" automaticamente — decisão por conjunto verificado em preview.

## Formatos

- Fonte editável: `.kra` (LFS). Entregável: `.png`. Não versionar `.kra~` (backup automático).
