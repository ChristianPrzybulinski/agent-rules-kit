# kit godot

Base para projetos Godot 4 2D.

| Arquivo | Uso |
|---|---|
| `.gitignore` | copiar para a raiz do projeto |
| `editor_settings_hints.md` | ajustes factuais de editor/projeto (pixel-art) |
| `scripts/make_spritesheet.py` | `python3 make_spritesheet.py <dir-frames> <saida.png>` — requer Pillow (`pip3 install --user pillow`); gera sheet + `<saida>.manifest.json` com sha256 de cada frame |
| `../git-lfs/.gitattributes` | combinar com o `.gitignore` (binários em LFS) |
| `../github/workflows/ci-godot.yml` | CI headless (import + GUT + export manual) |

Regras de GDScript/arquitetura de cenas: `agents/rules/godot/godot-2d.md` e `skills/godot/godot-standards`.
