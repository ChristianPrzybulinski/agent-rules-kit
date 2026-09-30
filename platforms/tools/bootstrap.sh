#!/usr/bin/env bash
# Primeira instalacao do kit. Uso: bootstrap.sh
# Idempotente: se ~/.ai-kit ja existe, apenas instala.
set -euo pipefail

KIT="$HOME/.ai-kit"
if [[ ! -d "$KIT" ]]; then
  if command -v gh >/dev/null 2>&1; then
    gh repo clone ChristianPrzybulinski/agent-rules-kit "$KIT"
  else
    git clone https://github.com/ChristianPrzybulinski/agent-rules-kit "$KIT"
  fi
fi
"$KIT/platforms/install/all.sh"
