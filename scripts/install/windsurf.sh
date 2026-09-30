#!/usr/bin/env bash
# Instala AGENTS.md como global rules do Windsurf.
set -euo pipefail
KIT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
mkdir -p "$HOME/.codeium/windsurf/memories"
cp "$KIT_DIR/AGENTS.md" "$HOME/.codeium/windsurf/memories/global_rules.md"
echo "windsurf: $HOME/.codeium/windsurf/memories/global_rules.md"
