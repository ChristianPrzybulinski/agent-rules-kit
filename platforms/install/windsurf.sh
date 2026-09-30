#!/usr/bin/env bash
# Installs AGENTS.md as the Windsurf global rules.
set -euo pipefail
KIT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
mkdir -p "$HOME/.codeium/windsurf/memories"
cp "$KIT_DIR/agents/AGENTS.md" "$HOME/.codeium/windsurf/memories/global_rules.md"
echo "windsurf: $HOME/.codeium/windsurf/memories/global_rules.md"
