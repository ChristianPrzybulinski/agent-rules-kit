#!/usr/bin/env bash
# Vendors third-party skills into agents/skills/vendor/<name>/ from the pinned lock.
# Usage: third-party.sh           installs/updates per platforms/kits/third-party/skills.lock
#        third-party.sh --check   fails if any VENDOR.md diverges from the lock
set -euo pipefail

KIT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
LOCK="$KIT_DIR/platforms/kits/third-party/skills.lock"
VENDOR="$KIT_DIR/agents/skills/vendor"
MODE="install"; [[ "${1:-}" == "--check" ]] && MODE="check"
FAILED=0

while IFS='|' read -r name repo path sha license verified; do
  name="$(echo "$name" | xargs)"; repo="$(echo "$repo" | xargs)"; path="$(echo "$path" | xargs)"
  sha="$(echo "$sha" | xargs)"; license="$(echo "$license" | xargs)"; verified="$(echo "$verified" | xargs)"
  [[ -z "$name" || "$name" == \#* ]] && continue
  dest="$VENDOR/$name"

  if [[ "$MODE" == check ]]; then
    [[ -f "$dest/VENDOR.md" ]] || { echo "FAIL: $name missing VENDOR.md" >&2; FAILED=1; continue; }
    grep -q "sha: $sha" "$dest/VENDOR.md" || { echo "FAIL: $name sha diverges from the lock" >&2; FAILED=1; }
    [[ -f "$dest/SKILL.md" ]] || { echo "FAIL: $name missing SKILL.md" >&2; FAILED=1; }
    continue
  fi

  tmp="$(mktemp -d)"
  git clone -q --depth 1 --filter=blob:none --sparse "https://github.com/$repo" "$tmp/repo" 2>/dev/null \
    || { echo "FAIL: clone of $repo" >&2; rm -rf "$tmp"; FAILED=1; continue; }
  (cd "$tmp/repo" && git sparse-checkout set --no-cone "$path" && { git checkout -q "$sha" 2>/dev/null || true; })
  src="$tmp/repo/$path"
  if [[ ! -f "$src/SKILL.md" ]]; then
    # depth 1 may not contain the sha if HEAD moved; pinned refetch
    (cd "$tmp/repo" && git fetch -q --depth 1 origin "$sha" && git checkout -q FETCH_HEAD)
  fi
  [[ -f "$src/SKILL.md" ]] || { echo "FAIL: SKILL.md missing in $repo:$path" >&2; rm -rf "$tmp"; FAILED=1; continue; }

  mkdir -p "$VENDOR"
  rm -rf "$dest"
  cp -R "$src" "$dest"
  cat > "$dest/VENDOR.md" <<EOF
repo: $repo
path: $path
sha: $sha
license: $license
verified: $verified

Do not edit — regenerate via platforms/install/third-party.sh.
EOF
  echo "vendor: $name <- $repo:$path @ ${sha:0:7}"
  rm -rf "$tmp"
done < "$LOCK"

if [[ "$MODE" == check ]]; then
  [[ $FAILED -eq 0 ]] && echo "third-party: lock consistent" || exit 1
fi
exit $FAILED
