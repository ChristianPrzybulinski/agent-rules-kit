#!/usr/bin/env bash
# Builds the kit as a Devin plugin (cloud sessions, Devin CLI, Devin Desktop).
# Usage: devin-plugin.sh <out-dir>   (<out-dir> must not exist or be empty)
#   <out-dir>/.devin-plugin/plugin.json   name ai-kit, version = VERSION
#   <out-dir>/AGENTS.md                   agents/AGENTS.md (always-on rule)
#   <out-dir>/skills/<name>/              agents/skills/**/<name>/ flattened (whole dir)
# Published to the devin-plugin branch by .github/workflows/devin-plugin.yml.
set -euo pipefail
KIT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
OUT="${1:?usage: devin-plugin.sh <out-dir>}"

if [[ -e "$OUT" && -n "$(ls -A "$OUT")" ]]; then
  echo "devin-plugin: $OUT is not empty" >&2
  exit 1
fi
mkdir -p "$OUT/.devin-plugin" "$OUT/skills"

version="$(cat "$KIT_DIR/VERSION")"
cat > "$OUT/.devin-plugin/plugin.json" <<JSON
{
  "name": "ai-kit",
  "version": "$version",
  "description": "agent-rules-kit: always-on global rules and skills (Clean Code, Clean Architecture, Java, Godot 2D, SDD, GitHub CLI)"
}
JSON

cp "$KIT_DIR/agents/AGENTS.md" "$OUT/AGENTS.md"

find "$KIT_DIR/agents/skills" -name SKILL.md | sort | while read -r f; do
  name="$(basename "$(dirname "$f")")"
  if [[ -e "$OUT/skills/$name" ]]; then
    echo "devin-plugin: duplicate skill name $name" >&2
    exit 1
  fi
  rsync -a "$(dirname "$f")/" "$OUT/skills/$name/"
done

echo "devin-plugin: ai-kit $version, $(find "$OUT/skills" -mindepth 2 -maxdepth 2 -name SKILL.md | wc -l | tr -d ' ') skills -> $OUT"
