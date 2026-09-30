#!/usr/bin/env bash
# Instala AGENTS.md global do Codex CLI.
# Doc oficial (https://developers.openai.com/codex/guides/agents-md): escopo
# global = ~/.codex/AGENTS.md (AGENTS.override.md tem precedencia; CODEX_HOME
# pode mudar o diretorio). Apenas cria/atualiza AGENTS.md — nao toca em mais nada.
set -euo pipefail
KIT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
DEST="${CODEX_HOME:-$HOME/.codex}"
mkdir -p "$DEST"
cp "$KIT_DIR/AGENTS.md" "$DEST/AGENTS.md"
if [[ -f "$DEST/AGENTS.override.md" ]]; then
  echo "codex: AGENTS.override.md existe e tem precedencia sobre AGENTS.md" >&2
fi
echo "codex: $DEST/AGENTS.md"
