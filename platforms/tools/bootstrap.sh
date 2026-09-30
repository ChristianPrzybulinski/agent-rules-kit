#!/usr/bin/env bash
# First kit installation. Usage: bootstrap.sh
# Idempotent: if ~/.ai-kit already exists, it only installs.
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
