#!/usr/bin/env bash
# Instala em todos os destinos e roda a validacao.
# --clean: apaga os destinos gerenciados antes (usado por refresh.sh em mudanca de layout).
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
KIT_DIR="$(cd "$HERE/../.." && pwd)"

if [[ "${1:-}" == "--clean" ]]; then
  rm -rf "$HOME/.devin/rules" "$HOME/.config/devin/skills"
  find "$HOME/.cursor/rules" -name '*.mdc' -delete 2>/dev/null || true
  find "${CODEX_HOME:-$HOME/.codex}/skills" -mindepth 2 -maxdepth 2 -name '.agent-rules-kit' -exec dirname {} \; 2>/dev/null | while read -r d; do rm -rf "$d"; done
  rm -f "$HOME/.codeium/windsurf/memories/global_rules.md"
  echo "clean: destinos gerenciados removidos"
fi

"$HERE/third-party.sh" --check
"$HERE/devin.sh"
"$HERE/cursor.sh"
"$HERE/windsurf.sh"
"$HERE/codex.sh"

# grava estado instalado (refresh.sh le isto para decidir reinstalacao)
STATE="$HOME/.config/agent-rules-kit"
mkdir -p "$STATE"
cp "$KIT_DIR/VERSION" "$KIT_DIR/LAYOUT_VERSION" "$STATE/"

"$KIT_DIR/platforms/tools/check.sh"
