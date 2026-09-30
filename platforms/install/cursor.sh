#!/usr/bin/env bash
# Converts agents/rules/<domain>/<name>.md (Devin/Windsurf frontmatter) into
# ~/.cursor/rules/<domain>-<name>.mdc (flattened name; Cursor frontmatter).
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
  rel="${f#"$KIT_DIR/agents/rules/"}"    # <domain>/<name>.md
  flat="${rel//\//-}"                   # <domain>-<name>.md
  convert "$f" "$DEST/${flat%.md}.mdc"
done

# removes obsolete .mdc files (e.g.: old names from before the restructure)
find "$DEST" -name '*.mdc' | while read -r f; do
  base="$(basename "$f" .mdc)"
  src_dom="${base%%-*}"                 # first component = domain
  src_name="${base#*-}.md"              # rest = name (may contain hyphens)
  [[ -f "$KIT_DIR/agents/rules/$src_dom/$src_name" ]] || { rm -f "$f"; echo "cursor: removed obsolete $f"; }
done

count=$(find "$DEST" -name '*.mdc' | wc -l | tr -d ' ')
echo "cursor: $count files -> $DEST"
