---
description: Versões Godot 4.x (4.7.2 instalada, imagem CI correspondente, TileMapLayer desde 4.3, política de releases). Carregar ao configurar projeto Godot ou CI.
trigger: model_decision
verified: "2026-09-29"
sources:
  - https://docs.godotengine.org/en/stable/about/release_policy.html
  - https://github.com/godotengine/godot/releases
---

# Godot 4 — versões

- Versão instalada nesta máquina: **4.7.2.stable** (`godot --version` → `4.7.2.stable.official.ed1daf0bf`).
- Imagem CI correspondente: `barichello/godot-ci:4.7.2` (tag existe no Docker Hub).
- Política de releases: Godot segue releases de feature (~4.x, alguns meses) + patch releases (4.x.y). Upgrades de minor podem quebrar compatibilidade de projetos — leia o changelog antes de migrar. Fonte: https://docs.godotengine.org/en/stable/about/release_policy.html
- `TileMapLayer` (nó separado, substitui camadas dentro de `TileMap`): introduzido no Godot **4.3**. Em projetos novos usar `TileMapLayer`; `TileMap` existe por compatibilidade.
- Downloads/releases: https://godotengine.org/download e https://github.com/godotengine/godot/releases.
