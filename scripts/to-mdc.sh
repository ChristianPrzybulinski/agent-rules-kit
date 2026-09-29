#!/usr/bin/env bash
# Converte rules/*.md (frontmatter Windsurf/Devin) para .mdc (frontmatter Cursor).
# Uso: to-mdc.sh [diretorio-destino]   (padrao: ~/.cursor/rules)
set -euo pipefail

KIT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DEST="${1:-$HOME/.cursor/rules}"
mkdir -p "$DEST"

convert() {
  local src="$1" dst="$2"
  awk '
    NR == 1 && $0 == "---" { in_fm = 1; print "---"; next }
    in_fm && $0 == "---" {
      if (!apply_set) print "alwaysApply: false"
      print "---"
      in_fm = 0
      next
    }
    in_fm {
      if ($0 ~ /^trigger:[[:space:]]*/) {
        val = $0
        sub(/^trigger:[[:space:]]*/, "", val)
        gsub(/["'"'"']/, "", val)
        if (val == "always_on") {
          print "alwaysApply: true"
        } else {
          print "alwaysApply: false"
          if ((val == "glob" || val == "globs") && globs != "") printf "%s", globs
        }
        apply_set = 1
        next
      }
      if ($0 ~ /^globs:[[:space:]]*/) { in_globs = 1; globs = $0 "\n"; next }
      if (in_globs && $0 ~ /^[[:space:]]+-/) { globs = globs $0 "\n"; next }
      in_globs = 0
      print
      next
    }
    { print }
  ' "$src" > "$dst"
}

count=0
for f in "$KIT_DIR"/rules/*.md; do
  name="$(basename "$f" .md)"
  convert "$f" "$DEST/$name.mdc"
  count=$((count + 1))
done
echo "to-mdc: $count arquivos -> $DEST"
