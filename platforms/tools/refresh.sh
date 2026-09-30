#!/usr/bin/env bash
# Updates the installed kit. Usage: refresh.sh [--quiet]
# pull --ff-only; compares the repo's VERSION/LAYOUT_VERSION with the installed
# state in ~/.config/agent-rules-kit/. Different LAYOUT -> full reinstall
# (--clean); only VERSION different -> reinstall; equal -> silence with --quiet.
set -euo pipefail

KIT="$HOME/.ai-kit"
STATE="$HOME/.config/agent-rules-kit"
QUIET=0; [[ "${1:-}" == "--quiet" ]] && QUIET=1
say() { if [[ $QUIET -eq 0 ]]; then echo "$@"; fi; }

[[ -d "$KIT" ]] || { say "refresh: $KIT does not exist; run platforms/tools/bootstrap.sh"; exit 0; }

if ! git -C "$KIT" pull --ff-only -q 2>/dev/null; then
  say "refresh: WARN: pull failed (network or divergence); using local state"
fi

repo_ver="$(cat "$KIT/VERSION" 2>/dev/null || echo 0)"
repo_layout="$(cat "$KIT/LAYOUT_VERSION" 2>/dev/null || echo 0)"
inst_ver="$(cat "$STATE/VERSION" 2>/dev/null || echo '')"
inst_layout="$(cat "$STATE/LAYOUT_VERSION" 2>/dev/null || echo '')"

if [[ "$repo_layout" != "$inst_layout" ]]; then
  say "refresh: layout $inst_layout -> $repo_layout; full reinstall"
  exec "$KIT/platforms/install/all.sh" --clean
elif [[ "$repo_ver" != "$inst_ver" ]]; then
  say "refresh: version $inst_ver -> $repo_ver; reinstalling"
  exec "$KIT/platforms/install/all.sh"
fi
exit 0
