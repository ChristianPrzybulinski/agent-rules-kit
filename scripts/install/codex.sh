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

# Skills: doc oficial (https://developers.openai.com/codex/skills e
# github.com/openai/codex docs/skills.md) — Codex le SKILL.md de
# ~/.codex/skills/**/SKILL.md (user scope, mantido por compatibilidade;
# ~/.agents/skills e a localizacao nova). Instalamos em $CODEX_HOME/skills.
# Marcador .agent-rules-kit: so gerenciamos/apagamos pastas marcadas por nos;
# .system e conteudo do usuario ficam intactos.
SKILLS_DEST="$DEST/skills"
mkdir -p "$SKILLS_DEST"
find "$KIT_DIR/skills" "$KIT_DIR/processes" -name SKILL.md | while read -r f; do
  name="$(basename "$(dirname "$f")")"
  mkdir -p "$SKILLS_DEST/$name"
  rsync -a --delete "$(dirname "$f")/" "$SKILLS_DEST/$name/"
  touch "$SKILLS_DEST/$name/.agent-rules-kit"
done
# remove pastas marcadas que nao estao mais no kit
find "$SKILLS_DEST" -mindepth 2 -maxdepth 2 -name '.agent-rules-kit' | while read -r m; do
  d="$(dirname "$m")"; name="$(basename "$d")"
  if ! find "$KIT_DIR/skills" "$KIT_DIR/processes" -type d -name "$name" | grep -q .; then
    rm -rf "$d" && echo "codex: skill removida $name"
  fi
done
echo "codex: skills em $SKILLS_DEST"
