#!/usr/bin/env bash
# Instala o kit no Devin:
#   agents/AGENTS.md            -> ~/.config/devin/AGENTS.md
#   agents/rules/<dom>/<n>.md   -> ~/.devin/rules/<dom>/<n>.md   (preserva subpastas)
#   agents/skills/**/SKILL.md   -> ~/.config/devin/skills/<basename>/  (achatado, diretorio inteiro)
# Remove ~/.devin/global_rules.md (duplica AGENTS.md no contexto).
set -euo pipefail

KIT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

mkdir -p "$HOME/.config/devin/skills" "$HOME/.devin/rules"
cp "$KIT_DIR/agents/AGENTS.md" "$HOME/.config/devin/AGENTS.md"
rsync -a --delete --exclude 'INDEX.md' "$KIT_DIR/agents/rules/" "$HOME/.devin/rules/"

# achata skills: cada pasta que contem SKILL.md vira ~/.config/devin/skills/<basename>
# (copia o diretorio inteiro: SKILL.md + scripts/ references/ assets/ etc.)
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT
find "$KIT_DIR/agents/skills" -name SKILL.md | while read -r f; do
  name="$(basename "$(dirname "$f")")"
  cp -R "$(dirname "$f")" "$tmp/$name"
done
rsync -a --delete "$tmp/" "$HOME/.config/devin/skills/"

rm -f "$HOME/.devin/global_rules.md"
echo "devin: AGENTS.md, $(find "$HOME/.devin/rules" -name '*.md' | wc -l | tr -d ' ') regras, $(find "$HOME/.config/devin/skills" -name SKILL.md | wc -l | tr -d ' ') skills"
