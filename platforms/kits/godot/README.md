# kit godot

Base for Godot 4 2D projects.

| File | Use |
|---|---|
| `.gitignore` | copy to the project root |
| `editor_settings_hints.md` | factual editor/project settings (pixel-art) |
| `scripts/make_spritesheet.py` | `python3 make_spritesheet.py <frames-dir> <output.png>` — requires Pillow (`pip3 install --user pillow`); generates sheet + `<output>.manifest.json` with each frame's sha256 |
| `gdlintrc` | copy to the project root as `.gdlintrc` (gdlint overrides only) |
| `requirements-gdtoolkit.txt` | copy to the project root; `pip install -r requirements-gdtoolkit.txt` gives `gdformat`/`gdlint` 4.5.0 |
| `scripts/keyed_csv_merge.py` | git merge driver for a keyed translation CSV (KIT-074), in place of `merge=union`, which kept a branch's stale row beside the other side's edited row of the same key and reported no conflict. `sync-project.sh` vendors it into `.github/merge-drivers/` for a godot profile; § Keyed-CSV merge driver |
| `../git-lfs/.gitattributes` | combine with the `.gitignore` (binaries in LFS) |
| `../github/workflows/ci-godot.yml` | headless CI through the `just` recipes of `../just/godot.just` (`just boot`, `just test`, `just lint`): import, boot proof, gdUnit4 by default or GUT, fails when no runner or zero tests, JUnit artifact, gdformat/gdlint, manual export |

GDScript and scene rules: `plugins/guardrails/rules/godot.md`; coding detail: `plugins/guardrails/skills/sdd-implement/references/godot/README.md`; design detail: `plugins/guardrails/skills/sdd-plan/references/godot/README.md`.

## Keyed-CSV merge driver

Each row of a Godot translation CSV is merged by its key: a key edited on one side takes the edit, keys added on both sides are both kept, and a key edited differently on both sides is a conflict written between git's markers at that key's place. The rule, the order kept and the fallback to a text merge are in the script's module text.

1. Mark each file once, in the repository's `.gitattributes` (replace a `merge=union` line on the same path):

   ```text
   client/resources/i18n/*.csv merge=keyed-csv
   ```

2. Configure the driver once per clone (git config is per clone and is not versioned; `sync-project.sh` prints these lines while the clone lacks them and never runs them; worktrees of one clone share it):

   ```bash
   git config merge.keyed-csv.name "keyed CSV merge"
   git config merge.keyed-csv.driver "python3 .github/merge-drivers/keyed_csv_merge.py --marker-size %L --path %P %O %A %B"
   ```

   Add `--key-column N` before `--marker-size` when the key is not in column 1. A clone without the driver merges the file as text, so a conflict still shows.
