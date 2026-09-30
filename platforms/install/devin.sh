#!/usr/bin/env bash
# Devin: global AGENTS.md only. Skills are read natively from ~/.agents/skills
# (installed by skills.sh). Removes the legacy kit destinations:
#   ~/.devin/global_rules.md, ~/.devin/rules/ (kit-owned) and kit-named folders in
#   ~/.config/devin/skills/ (that dir was fully managed by rsync --delete — only
#   folders matching a current kit skill name are removed).
set -euo pipefail
KIT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

mkdir -p "$HOME/.config/devin"
cp "$KIT_DIR/agents/AGENTS.md" "$HOME/.config/devin/AGENTS.md"
echo "devin: $HOME/.config/devin/AGENTS.md"

rm -f "$HOME/.devin/global_rules.md"
if [[ -d "$HOME/.devin/rules" ]]; then
  rm -rf "$HOME/.devin/rules" && echo "devin: removed legacy ~/.devin/rules"
fi

LEGACY="$HOME/.config/devin/skills"
if [[ -d "$LEGACY" ]]; then
  find "$KIT_DIR/agents/skills" -name SKILL.md | while read -r f; do
    name="$(basename "$(dirname "$f")")"
    if [[ -d "$LEGACY/$name" ]]; then
      rm -rf "${LEGACY:?}/$name" && echo "devin: removed legacy skill $name from ~/.config/devin/skills"
    fi
  done
  echo "devin: notice — ~/.config/devin/skills is no longer a kit destination; skills live in ~/.agents/skills"
fi
