# kit godot

Base for Godot 4 2D projects.

| File | Use |
|---|---|
| `.gitignore` | copy to the project root |
| `editor_settings_hints.md` | factual editor/project settings (pixel-art) |
| `scripts/make_spritesheet.py` | `python3 make_spritesheet.py <frames-dir> <output.png>` — requires Pillow (`pip3 install --user pillow`); generates sheet + `<output>.manifest.json` with each frame's sha256 |
| `gdlintrc` | copy to the project root as `.gdlintrc` (gdlint overrides only) |
| `requirements-gdtoolkit.txt` | copy to the project root; `pip install -r requirements-gdtoolkit.txt` gives `gdformat`/`gdlint` 4.5.0 |
| `../git-lfs/.gitattributes` | combine with the `.gitignore` (binaries in LFS) |
| `../github/workflows/ci-godot.yml` | headless CI (import, boot proof, gdUnit4 by default or GUT, fails when no runner or zero tests, JUnit artifact, gdformat/gdlint, manual export) |

GDScript/scene-architecture rules: `plugins/dev/skills/godot-standards/SKILL.md`.
