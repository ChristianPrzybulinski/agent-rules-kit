#!/usr/bin/env bash
# Installs the kit into Devin:
#   agents/AGENTS.md            -> ~/.config/devin/AGENTS.md
#   agents/rules/<dom>/<n>.md   -> ~/.devin/rules/<dom>/<n>.md   (preserves subfolders)
#   agents/skills/**/SKILL.md   -> ~/.config/devin/skills/<basename>/  (flattened, whole directory)
# Removes ~/.devin/global_rules.md (duplicates AGENTS.md in the context).
set -euo pipefail

KIT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

mkdir -p "$HOME/.config/devin/skills" "$HOME/.devin/rules"
cp "$KIT_DIR/agents/AGENTS.md" "$HOME/.config/devin/AGENTS.md"
rsync -a --delete --exclude 'INDEX.md' "$KIT_DIR/agents/rules/" "$HOME/.devin/rules/"

# flattens skills: each folder containing SKILL.md becomes ~/.config/devin/skills/<basename>
# (copies the whole directory: SKILL.md + scripts/ references/ assets/ etc.)
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT
find "$KIT_DIR/agents/skills" -name SKILL.md | while read -r f; do
  name="$(basename "$(dirname "$f")")"
  cp -R "$(dirname "$f")" "$tmp/$name"
done
rsync -a --delete "$tmp/" "$HOME/.config/devin/skills/"

rm -f "$HOME/.devin/global_rules.md"
echo "devin: AGENTS.md, $(find "$HOME/.devin/rules" -name '*.md' | wc -l | tr -d ' ') rules, $(find "$HOME/.config/devin/skills" -name SKILL.md | wc -l | tr -d ' ') skills"
