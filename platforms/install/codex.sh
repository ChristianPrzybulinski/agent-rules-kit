#!/usr/bin/env bash
# Installs the Codex CLI global AGENTS.md.
# Official doc (https://developers.openai.com/codex/guides/agents-md): global
# scope = ~/.codex/AGENTS.md (AGENTS.override.md takes precedence; CODEX_HOME
# can change the directory).
# Skills: Codex reads $HOME/.agents/skills (https://developers.openai.com/codex/skills),
# installed by skills.sh. Here we only remove legacy kit-marked folders left in
# $CODEX_HOME/skills (user/unmarked content stays intact).
set -euo pipefail
KIT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
DEST="${CODEX_HOME:-$HOME/.codex}"
mkdir -p "$DEST"
cp "$KIT_DIR/agents/AGENTS.md" "$DEST/AGENTS.md"
if [[ -f "$DEST/AGENTS.override.md" ]]; then
  echo "codex: AGENTS.override.md exists and takes precedence over AGENTS.md" >&2
fi
echo "codex: $DEST/AGENTS.md"

LEGACY="$DEST/skills"
if [[ -d "$LEGACY" ]]; then
  find "$LEGACY" -mindepth 2 -maxdepth 2 -name '.agent-rules-kit' | while read -r m; do
    d="$(dirname "$m")"
    rm -rf "$d" && echo "codex: removed legacy skill $(basename "$d") from $LEGACY"
  done
fi
