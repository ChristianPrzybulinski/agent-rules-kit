#!/usr/bin/env bash
# Instala o kit no Devin:
#   AGENTS.md            -> ~/.config/devin/AGENTS.md
#   rules/<dom>/<n>.md   -> ~/.devin/rules/<dom>/<n>.md   (preserva subpastas)
#   skills/**/SKILL.md   -> ~/.config/devin/skills/<basename>/  (achatado)
#   processes/**/SKILL.md -> idem
# Remove ~/.devin/global_rules.md (duplica AGENTS.md no contexto).
set -euo pipefail

KIT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

mkdir -p "$HOME/.config/devin/skills" "$HOME/.devin/rules"
cp "$KIT_DIR/AGENTS.md" "$HOME/.config/devin/AGENTS.md"
rsync -a --delete "$KIT_DIR/rules/" "$HOME/.devin/rules/"

# achata skills: cada pasta que contem SKILL.md vira ~/.config/devin/skills/<basename>
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT
find "$KIT_DIR/skills" "$KIT_DIR/processes" -name SKILL.md | while read -r f; do
  name="$(basename "$(dirname "$f")")"
  mkdir -p "$tmp/$name"
  cp "$f" "$tmp/$name/SKILL.md"
done
rsync -a --delete "$tmp/" "$HOME/.config/devin/skills/"

rm -f "$HOME/.devin/global_rules.md"
echo "devin: AGENTS.md, $(find "$HOME/.devin/rules" -name '*.md' | wc -l | tr -d ' ') regras, $(find "$HOME/.config/devin/skills" -name SKILL.md | wc -l | tr -d ' ') skills"
