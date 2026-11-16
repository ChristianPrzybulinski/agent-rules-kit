#!/usr/bin/env bash
# The release the user install follows, for bootstrap.sh, refresh.sh and doctor.sh, which source this file (#271).
# Usage: kit-release.sh [kit-dir]   prints the newest release tag of the kit clone; exit 1 when there is none

# shellcheck disable=SC2034  # read by the scripts that source this file
KIT_REPOSITORY="ChristianPrzybulinski/agent-rules-kit"

# The newest vX.Y.Z tag on origin/main. The clone (and with it the always-on ~/.claude/CLAUDE.md and
# ~/.codex/AGENTS.md links), the Codex marketplace and Devin's plugin follow it, so a kit merge reaches the
# machine with its release, as a resync PR brings it to a vendored project (KIT-072).
kit_release_tag() {
  { git -C "$1" tag --list 'v*' --merged origin/main --sort=-v:refname 2>/dev/null || true; } \
    | awk '/^v[0-9]+\.[0-9]+\.[0-9]+$/ && !found { print; found = 1 }'
}

# The ref of the ai-kit marketplace in Codex's config.toml; "<absent>" when it has none.
codex_kit_ref() {
  python3 - "${CODEX_HOME:-$HOME/.codex}/config.toml" <<'PY'
import re
import sys

try:
    lines = open(sys.argv[1], encoding="utf-8").read().splitlines()
except OSError:
    lines = []
table, ref = None, None
for line in lines:
    stripped = line.strip()
    if stripped.startswith("["):
        table = stripped.replace('"', "")
    elif table == "[marketplaces.ai-kit]":
        match = re.match(r"ref\s*=\s*[\"']([^\"']*)[\"']", stripped)
        if match:
            ref = match.group(1)
print(ref or "<absent>")
PY
}

if [[ "${BASH_SOURCE[0]}" == "$0" ]]; then
  tag="$(kit_release_tag "${1:-${AI_KIT_DIR:-$HOME/.ai-kit}}")"
  [[ -n "$tag" ]] || exit 1
  printf '%s\n' "$tag"
fi
