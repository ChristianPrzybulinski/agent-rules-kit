#!/usr/bin/env bash
# Installs the Codex CLI global AGENTS.md.
# Official doc (https://developers.openai.com/codex/guides/agents-md): global
# scope = ~/.codex/AGENTS.md (AGENTS.override.md takes precedence; CODEX_HOME
# can change the directory).
set -euo pipefail
KIT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
DEST="${CODEX_HOME:-$HOME/.codex}"
mkdir -p "$DEST"
cp "$KIT_DIR/agents/AGENTS.md" "$DEST/AGENTS.md"
if [[ -f "$DEST/AGENTS.override.md" ]]; then
  echo "codex: AGENTS.override.md exists and takes precedence over AGENTS.md" >&2
fi
echo "codex: $DEST/AGENTS.md"

# Skills: official doc (https://developers.openai.com/codex/skills and
# github.com/openai/codex docs/skills.md) — Codex reads SKILL.md from
# ~/.codex/skills/**/SKILL.md (user scope, kept for compatibility;
# ~/.agents/skills is the new location). We install into $CODEX_HOME/skills.
# Marker .agent-rules-kit: we only manage/delete folders we marked;
# .system and user content stay intact.
SKILLS_DEST="$DEST/skills"
mkdir -p "$SKILLS_DEST"
find "$KIT_DIR/agents/skills" -name SKILL.md | while read -r f; do
  name="$(basename "$(dirname "$f")")"
  mkdir -p "$SKILLS_DEST/$name"
  rsync -a --delete "$(dirname "$f")/" "$SKILLS_DEST/$name/"
  touch "$SKILLS_DEST/$name/.agent-rules-kit"
done
# removes marked folders no longer in the kit
find "$SKILLS_DEST" -mindepth 2 -maxdepth 2 -name '.agent-rules-kit' | while read -r m; do
  d="$(dirname "$m")"; name="$(basename "$d")"
  if ! find "$KIT_DIR/agents/skills" -mindepth 2 -maxdepth 2 -type d -name "$name" | grep -q .; then
    rm -rf "$d" && echo "codex: skill removed $name"
  fi
done
echo "codex: skills in $SKILLS_DEST"
