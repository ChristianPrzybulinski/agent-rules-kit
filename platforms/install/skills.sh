#!/usr/bin/env bash
# Installs kit skills into the native skills destinations shared by the tools:
#   agents/skills/**/SKILL.md -> ~/.agents/skills/<name>/        (Devin, Cursor, Codex)
#                           and -> ~/.codeium/windsurf/skills/<name>/
# Copies the whole skill directory, flattened by basename (names are unique in the kit).
# Marker .agent-rules-kit: we only manage/delete folders we marked; user/third-party
# skills in those dirs stay intact.
set -euo pipefail
KIT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

install_into() {
  local dest="$1" f name d m
  mkdir -p "$dest"
  find "$KIT_DIR/agents/skills" -name SKILL.md | while read -r f; do
    name="$(basename "$(dirname "$f")")"
    mkdir -p "$dest/$name"
    rsync -a --delete "$(dirname "$f")/" "$dest/$name/"
    touch "$dest/$name/.agent-rules-kit"
  done
  # removes marked folders no longer in the kit
  find "$dest" -mindepth 2 -maxdepth 2 -name '.agent-rules-kit' | while read -r m; do
    d="$(dirname "$m")"; name="$(basename "$d")"
    if ! find "$KIT_DIR/agents/skills" -mindepth 2 -maxdepth 2 -type d -name "$name" | grep -q .; then
      rm -rf "$d" && echo "skills: removed $name from $dest"
    fi
  done
}

install_into "$HOME/.agents/skills"
install_into "$HOME/.codeium/windsurf/skills"
echo "skills: $(find "$KIT_DIR/agents/skills" -name SKILL.md | wc -l | tr -d ' ') skills -> ~/.agents/skills + ~/.codeium/windsurf/skills"
