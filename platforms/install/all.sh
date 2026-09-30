#!/usr/bin/env bash
# Installs into all destinations and runs validation.
# --clean: deletes the managed destinations first (used by refresh.sh on a layout change).
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
KIT_DIR="$(cd "$HERE/../.." && pwd)"

# legacy v4 cleanup; remove after 6.x — basenames <dom>-<name> of the rules that
# used to be converted into ~/.cursor/rules/*.mdc (Cursor now reads
# ~/.agents/skills natively).
LEGACY_CURSOR_RULES=(
  architecture-clean-architecture architecture-ddd-and-patterns
  core-evidence core-sessions core-tokens
  development-clean-code development-simplicity development-testing development-twelve-factor
  documentation-documentation documentation-living-docs
  git-branching-and-versioning git-git-lfs-and-binaries git-github-cli
  godot-godot-2d java-build-and-dependencies java-java
  security-secure-development
)

clean_legacy_cursor() {
  local dir="$HOME/.cursor/rules" f base known
  [[ -d "$dir" ]] || return 0
  for f in "$dir"/*.mdc; do
    [[ -f "$f" ]] || continue
    # kit-generated files always carry an alwaysApply: line in the frontmatter
    head -n 5 "$f" | grep -q 'alwaysApply:' || continue
    base="$(basename "$f" .mdc)"
    for known in "${LEGACY_CURSOR_RULES[@]}"; do
      if [[ "$base" == "$known" ]]; then
        rm -f "$f" && echo "cursor: removed legacy $f"
      fi
    done
  done
}

if [[ "${1:-}" == "--clean" ]]; then
  rm -rf "$HOME/.devin/rules" "$HOME/.config/devin/skills"
  for skills_dir in "$HOME/.agents/skills" "$HOME/.codeium/windsurf/skills" "${CODEX_HOME:-$HOME/.codex}/skills"; do
    [[ -d "$skills_dir" ]] || continue
    find "$skills_dir" -mindepth 2 -maxdepth 2 -name '.agent-rules-kit' -exec dirname {} \; 2>/dev/null | while read -r d; do rm -rf "$d"; done
  done
  rm -f "$HOME/.codeium/windsurf/memories/global_rules.md"
  echo "clean: managed destinations removed"
fi

"$HERE/third-party.sh" --check
"$HERE/skills.sh"
"$HERE/devin.sh"
"$HERE/windsurf.sh"
"$HERE/codex.sh"
clean_legacy_cursor

# records installed state (refresh.sh reads this to decide on a reinstall)
STATE="$HOME/.config/agent-rules-kit"
mkdir -p "$STATE"
cp "$KIT_DIR/VERSION" "$KIT_DIR/LAYOUT_VERSION" "$STATE/"

"$KIT_DIR/platforms/tools/check.sh"
