#!/usr/bin/env bash
# Scaffold for the eval case: a throwaway git repository in the empty workspace.
set -euo pipefail
git init -q .
git config user.email eval@example.invalid
git config user.name eval
mkdir -p notes
printf '# Godot 4 notes\n\nTileMap is deprecated since 4.3 in favour of TileMapLayer, but the node still exists in 4.7.\n' > notes/godot-4-versions.md
git add -A
git commit -q -m 'base'
