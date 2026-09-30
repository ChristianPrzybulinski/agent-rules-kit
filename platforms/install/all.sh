#!/usr/bin/env bash
# Installs into all destinations and runs validation.
# --clean: deletes the managed destinations first (used by refresh.sh on a layout change).
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
KIT_DIR="$(cd "$HERE/../.." && pwd)"

if [[ "${1:-}" == "--clean" ]]; then
  rm -rf "$HOME/.devin/rules" "$HOME/.config/devin/skills"
  find "$HOME/.cursor/rules" -name '*.mdc' -delete 2>/dev/null || true
  find "${CODEX_HOME:-$HOME/.codex}/skills" -mindepth 2 -maxdepth 2 -name '.agent-rules-kit' -exec dirname {} \; 2>/dev/null | while read -r d; do rm -rf "$d"; done
  rm -f "$HOME/.codeium/windsurf/memories/global_rules.md"
  echo "clean: managed destinations removed"
fi

"$HERE/third-party.sh" --check
"$HERE/devin.sh"
"$HERE/cursor.sh"
"$HERE/windsurf.sh"
"$HERE/codex.sh"

# records installed state (refresh.sh reads this to decide on a reinstall)
STATE="$HOME/.config/agent-rules-kit"
mkdir -p "$STATE"
cp "$KIT_DIR/VERSION" "$KIT_DIR/LAYOUT_VERSION" "$STATE/"

"$KIT_DIR/platforms/tools/check.sh"
