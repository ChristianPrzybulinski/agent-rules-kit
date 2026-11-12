#!/usr/bin/env bash
# Updates the kit clone plus Codex and Claude marketplace plugins. Usage: refresh.sh
set -euo pipefail

KIT="${AI_KIT_DIR:-$HOME/.ai-kit}"
source "$(dirname "${BASH_SOURCE[0]}")/codex-bin.sh"

warn() {
  printf 'WARN: refresh: %s\n' "$*" >&2
}

fail() {
  printf 'FAIL: refresh: %s\n' "$*" >&2
  exit 1
}

json_contains() {
  local payload="$1"
  local needle="$2"
  python3 - "$needle" "$payload" <<'PY'
import json
import sys

try:
    data = json.loads(sys.argv[2])
except json.JSONDecodeError:
    raise SystemExit(1)
needle = sys.argv[1]
def contains(value):
    if isinstance(value, str):
        return value == needle
    if isinstance(value, list):
        return any(contains(item) for item in value)
    if isinstance(value, dict):
        return any(contains(item) for item in value.values())
    return False
raise SystemExit(0 if contains(data) else 1)
PY
}

# KIT-013: Claude caches a plugin per version, so a kit change without a version bump leaves the cache stale.
# Prints each user-scope <plugin>@ai-kit whose cache differs from its directory in the marketplace clone.
claude_stale_plugins() {
  python3 - "$1" "$2" <<'PY'
import hashlib
import json
import os
import sys
from pathlib import Path

RUNTIME_MARKERS = {".in_use"}

def tree_hash(root):
    digest = hashlib.sha256()
    for directory, dirs, files in os.walk(root):
        if Path(directory) == root:
            # Claude keeps its .in_use process markers at the top of a cache directory.
            dirs[:] = [name for name in dirs if name not in RUNTIME_MARKERS]
            files = [name for name in files if name not in RUNTIME_MARKERS]
        dirs.sort()
        for name in sorted(files):
            path = Path(directory, name)
            relative = path.relative_to(root)
            digest.update(str(relative).encode() + b"\0")
            digest.update(b"link:" + os.readlink(path).encode() if path.is_symlink() else path.read_bytes())
            digest.update(b"\0")
    return digest.hexdigest()

try:
    marketplaces = json.loads(sys.argv[1])
    plugins = json.loads(sys.argv[2])
except json.JSONDecodeError:
    raise SystemExit(0)
if not isinstance(marketplaces, list) or not isinstance(plugins, list):
    raise SystemExit(0)
location = next((m.get("installLocation") for m in marketplaces if m.get("name") == "ai-kit"), None)
if not location:
    raise SystemExit(0)
try:
    catalog = json.loads(Path(location, ".claude-plugin/marketplace.json").read_text(encoding="utf-8"))
except (OSError, json.JSONDecodeError):
    raise SystemExit(0)
sources = {entry.get("name"): entry.get("source") for entry in catalog.get("plugins", [])}
stale = set()
for plugin in plugins:
    name, _, marketplace = str(plugin.get("id", "")).partition("@")
    source = sources.get(name)
    install = plugin.get("installPath")
    if marketplace != "ai-kit" or plugin.get("scope", "user") != "user" or not isinstance(source, str) or not install:
        continue
    source_dir = Path(location, source)
    if source_dir.is_dir() and (not Path(install).is_dir() or tree_hash(source_dir) != tree_hash(Path(install))):
        stale.add(name)
for name in sorted(stale):
    print(name)
PY
}

run_step() {
  local label="$1"
  local output
  shift
  if ! output="$("$@" 2>&1)"; then
    [[ -z "$output" ]] || printf '%s\n' "$output" >&2
    fail "$label"
  fi
}

[[ -d "$KIT/.git" ]] || fail "$KIT is not a git clone — run platforms/tools/bootstrap.sh"

# KIT-046: the pull replaces this script, but bash keeps running the copy it opened, so a run that pulls a new
# refresh.sh would finish with the old logic. Hand over once to the pulled script, which skips the pull.
if [[ "${AI_KIT_REFRESH_PULLED:-0}" != "1" ]]; then
  run_step "git fetch origin failed" git -C "$KIT" fetch origin

  branch="$(git -C "$KIT" branch --show-current)" || fail "cannot read current branch"
  status="$(git -C "$KIT" status --short)" || fail "cannot read git status"
  if [[ -n "$status" ]]; then
    printf 'FAIL: refresh: working tree is dirty; refusing to update\n%s\n' "$status" >&2
    exit 1
  fi

  if [[ "$branch" != "main" ]]; then
    run_step "cannot checkout main" git -C "$KIT" checkout main
  fi

  before="$(git -C "$KIT" rev-parse HEAD)" || fail "cannot read HEAD"
  run_step "git pull --ff-only failed" git -C "$KIT" pull --ff-only
  if ! git -C "$KIT" diff --quiet "$before" HEAD -- platforms/tools/refresh.sh platforms/tools/codex-bin.sh; then
    printf 'refresh: the pull changed refresh.sh; running the new version\n'
    exec env AI_KIT_REFRESH_PULLED=1 bash "$KIT/platforms/tools/refresh.sh" "$@"
  fi
fi

codex="$(codex_bin || true)"
if [[ -n "$codex" ]]; then
  marketplaces="$("$codex" plugin marketplace list 2>/dev/null || true)"
  if [[ "$marketplaces" == *"ai-kit"* ]]; then
    run_step "codex marketplace upgrade failed" "$codex" plugin marketplace upgrade ai-kit
  else
    warn "codex marketplace ai-kit not registered — run platforms/tools/bootstrap.sh"
  fi
else
  printf 'skip: refresh: no codex CLI found; Codex marketplace not upgraded\n'
fi

if command -v claude >/dev/null 2>&1; then
  claude_marketplaces="$(claude plugin marketplace list --json 2>/dev/null || true)"
  if json_contains "$claude_marketplaces" "ai-kit"; then
    run_step "claude marketplace update failed" claude plugin marketplace update ai-kit --json
    claude_plugins="$(claude plugin list --json 2>/dev/null || true)"
    for plugin_dir in "$KIT"/plugins/*/; do
      plugin_name="$(basename "$plugin_dir")"
      [[ -d "$plugin_dir/.claude-plugin" ]] || continue
      if json_contains "$claude_plugins" "$plugin_name@ai-kit"; then
        run_step "claude plugin update failed for $plugin_name" claude plugin update "$plugin_name@ai-kit" --json
      else
        # KIT-038: a plugin renamed in the marketplace's renames map is enabled but not cached until installed once
        run_step "claude plugin install failed for $plugin_name — run: claude plugin install $plugin_name@ai-kit" \
          claude plugin install "$plugin_name@ai-kit" --json
        printf 'refresh: installed Claude plugin %s@ai-kit\n' "$plugin_name"
      fi
    done
    claude_plugins="$(claude plugin list --json 2>/dev/null || true)"
    stale_plugins="$(claude_stale_plugins "$claude_marketplaces" "$claude_plugins")" \
      || fail "cannot compare Claude plugin caches with the kit"
    for plugin_name in $stale_plugins; do
      run_step "claude plugin uninstall failed for $plugin_name" \
        claude plugin uninstall "$plugin_name@ai-kit" --keep-data --json
      run_step "claude plugin install failed for $plugin_name — run: claude plugin install $plugin_name@ai-kit" \
        claude plugin install "$plugin_name@ai-kit" --json
      printf 'refresh: reinstalled Claude plugin %s@ai-kit (cache differed from the kit)\n' "$plugin_name"
    done
  else
    warn "claude marketplace ai-kit not registered — run platforms/tools/bootstrap.sh"
  fi
else
  # Under launchd PATH is the plist's, not the login shell's; print it so a missing entry shows (KIT-022)
  printf 'skip: refresh: claude CLI not found on PATH %s; Claude plugins not updated\n' "$PATH"
fi

sha="$(git -C "$KIT" rev-parse --short HEAD)" || fail "cannot read HEAD"
date="$(git -C "$KIT" show -s --format=%cs HEAD)" || fail "cannot read commit date"
printf 'refresh: %s %s main\n' "$sha" "$date"
