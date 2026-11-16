#!/usr/bin/env bash
# The release and the branch the user install follows, for bootstrap.sh, refresh.sh and doctor.sh, which source this
# file (#271, KIT-081).
# Usage: kit-release.sh [kit-dir]   prints the newest release tag of the kit clone; exit 1 when there is none

# shellcheck disable=SC2034  # read by the scripts that source this file
KIT_REPOSITORY="ChristianPrzybulinski/agent-rules-kit"
# KIT-081: the branch every install follows. release.yml moves it to each release (fast-forward only), so Claude
# Code's and Codex's marketplaces and Devin's plugin name it once and reach each release by a plain update.
# shellcheck disable=SC2034  # read by the scripts that source this file
KIT_STABLE_BRANCH="stable"

# The newest vX.Y.Z tag on origin/main. The clone (and with it the always-on ~/.claude/CLAUDE.md and
# ~/.codex/AGENTS.md links) checks it out, and `stable` points at it once release.yml has run, so a kit merge
# reaches the machine with its release, as a resync PR brings it to a vendored project (KIT-072).
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

# Claude Code's plugin folder: known_marketplaces.json, installed_plugins.json and data/ (2.1.287 moves all three
# with CLAUDE_CODE_PLUGIN_CACHE_DIR, else with CLAUDE_CONFIG_DIR).
claude_plugins_root() {
  printf '%s\n' "${CLAUDE_CODE_PLUGIN_CACHE_DIR:-${CLAUDE_CONFIG_DIR:-$HOME/.claude}/plugins}"
}

# The ref of Claude Code's ai-kit marketplace in known_marketplaces.json; "<absent>" when it has none (KIT-081).
claude_kit_ref() {
  python3 - "$(claude_plugins_root)/known_marketplaces.json" <<'PY'
import json
import sys

try:
    with open(sys.argv[1], encoding="utf-8") as handle:
        data = json.load(handle)
except (OSError, ValueError):
    data = None
entry = data.get("ai-kit") if isinstance(data, dict) else None
source = entry.get("source") if isinstance(entry, dict) else None
ref = source.get("ref") if isinstance(source, dict) else None
print(ref if isinstance(ref, str) and ref else "<absent>")
PY
}

if [[ "${BASH_SOURCE[0]}" == "$0" ]]; then
  tag="$(kit_release_tag "${1:-${AI_KIT_DIR:-$HOME/.ai-kit}}")"
  [[ -n "$tag" ]] || exit 1
  printf '%s\n' "$tag"
fi
