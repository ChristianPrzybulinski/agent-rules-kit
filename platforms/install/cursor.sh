#!/usr/bin/env bash
# Converte agents/rules/<dominio>/<nome>.md (frontmatter Devin/Windsurf) para
# ~/.cursor/rules/<dominio>-<nome>.mdc (nome achatado; frontmatter Cursor).
set -euo pipefail

KIT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
DEST="${1:-$HOME/.cursor/rules}"
mkdir -p "$DEST"

convert() {
  awk '
    NR == 1 && $0 == "---" { in_fm = 1; print "---"; next }
    in_fm && $0 == "---" {
      if (!apply_set) print "alwaysApply: false"
      print "---"; in_fm = 0; next
    }
    in_fm {
      if ($0 ~ /^trigger:[[:space:]]*/) {
        val = $0; sub(/^trigger:[[:space:]]*/, "", val); gsub(/["'"'"']/, "", val)
        if (val == "always_on") print "alwaysApply: true"
        else {
          print "alwaysApply: false"
          if ((val == "glob" || val == "globs") && globs != "") printf "%s", globs
        }
        apply_set = 1; next
      }
      if ($0 ~ /^globs:[[:space:]]*/) { in_globs = 1; globs = $0 "\n"; next }
      if (in_globs && $0 ~ /^[[:space:]]+-/) { globs = globs $0 "\n"; next }
      in_globs = 0
      print; next
    }
    { print }
  ' "$1" > "$2"
}

find "$KIT_DIR/agents/rules" -name '*.md' ! -name 'INDEX.md' | while read -r f; do
  rel="${f#"$KIT_DIR/agents/rules/"}"    # <dominio>/<nome>.md
  flat="${rel//\//-}"                   # <dominio>-<nome>.md
  convert "$f" "$DEST/${flat%.md}.mdc"
done

# remove .mdc obsoletos (ex.: nomes antigos pre-reestruturacao)
find "$DEST" -name '*.mdc' | while read -r f; do
  base="$(basename "$f" .mdc)"
  src_dom="${base%%-*}"                 # primeiro componente = dominio
  src_name="${base#*-}.md"              # resto = nome (pode ter hifens)
  [[ -f "$KIT_DIR/agents/rules/$src_dom/$src_name" ]] || { rm -f "$f"; echo "cursor: removido obsoleto $f"; }
done

count=$(find "$DEST" -name '*.mdc' | wc -l | tr -d ' ')
echo "cursor: $count arquivos -> $DEST"
