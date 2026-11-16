# kit godot

Base for Godot 4 2D projects.

| File | Use |
|---|---|
| `.gitignore` | copy to the project root |
| `gdlintrc` | copy to the project root as `.gdlintrc` (gdlint overrides only) |
| `requirements-gdtoolkit.txt` | copy to the project root; `pip install -r requirements-gdtoolkit.txt` gives `gdformat`/`gdlint` 4.5.0 |
| `scripts/keyed_csv_merge.py` | git merge driver for a keyed translation CSV (KIT-074), in place of `merge=union`, which kept a branch's stale row beside the other side's edited row of the same key and reported no conflict. git runs it from the installed kit (`~/.ai-kit`, KIT-081 stage 1b: no copy in the project); § Keyed-CSV merge driver |
| `../git-lfs/.gitattributes` | combine with the `.gitignore` (binaries in LFS) |
| `../github/workflows/ci-godot.yml` | headless CI through the `just` recipes of `../just/godot.just` (`just boot`, `just test`, `just lint`): import, boot proof, gdUnit4 by default or GUT, fails when no runner or zero tests, JUnit artifact, gdformat/gdlint, manual export |

GDScript and scene rules: `plugins/guardrails/rules/godot.md`; coding detail: `plugins/guardrails/skills/sdd-implement/references/godot/README.md`; design detail: `plugins/guardrails/skills/sdd-plan/references/godot/README.md`.

## Keyed-CSV merge driver

Each row of a Godot translation CSV is merged by its key: a key edited on one side takes the edit, keys added on both sides are both kept, and a key edited differently on both sides is a conflict written between git's markers at that key's place. The rule, the order kept and the fallback to a text merge are in the script's module text.

1. Mark each file once, in the repository's `.gitattributes` (replace a `merge=union` line on the same path):

   ```text
   client/resources/i18n/*.csv merge=keyed-csv
   ```

2. Configure the driver once per clone (git config is per clone and is not versioned; `sync-project.sh` prints these lines for a godot profile while the clone lacks them, or still runs the `.github/merge-drivers/` copy older syncs vendored, and never runs them; worktrees of one clone share it). git runs the driver through `sh`, which expands `~`, so it runs the installed kit's file:

   ```bash
   git config merge.keyed-csv.name "keyed CSV merge"
   git config merge.keyed-csv.driver "python3 ~/.ai-kit/platforms/kits/godot/scripts/keyed_csv_merge.py --marker-size %L --path %P %O %A %B"
   ```

   Since KIT-081 stage 1b the project holds no copy of the driver: `sync-project.sh` removes the `.github/merge-drivers/keyed_csv_merge.py` it once vendored (only that kit-marked file; a project's own driver there stays), and `--check` fails while the clone's config still runs it.

   Add `--key-column N` before `--marker-size` when the key is not in column 1. A clone without the driver merges the file as text, so a conflict still shows. So does the driver, with a warning, when a side does not parse as CSV (a quoted field left open at the end); the csv module splits the records, so an inch mark inside an unquoted field (`5" screen`) parses. A blank line has no key, so the merged file drops it.
