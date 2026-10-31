#!/usr/bin/env bash
# Installs the plugin-first kit on this machine. Usage: bootstrap.sh
set -euo pipefail

KIT="${AI_KIT_DIR:-$HOME/.ai-kit}"
source "$(dirname "${BASH_SOURCE[0]}")/codex-bin.sh"
SRC="${AI_KIT_SOURCE:-https://github.com/ChristianPrzybulinski/agent-rules-kit}"
REPOSITORY="ChristianPrzybulinski/agent-rules-kit"
HEADER="# Global Rules — AI Kit"

warn() {
  printf 'WARN: bootstrap: %s\n' "$*" >&2
}

fail() {
  printf 'FAIL: bootstrap: %s\n' "$*" >&2
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

ensure_agents_link() {
  local destination="$HOME/.codex/AGENTS.md"
  local expected="$KIT/plugins/core/AGENTS.md"
  local current
  local backup
  mkdir -p "$HOME/.codex"
  if [[ -L "$destination" ]]; then
    current="$(readlink "$destination")"
    if [[ "$current" == "$expected" ]]; then
      printf 'ok: codex AGENTS.md symlink\n'
    elif [[ "$current" == "$KIT/"* ]]; then
      rm "$destination"
      ln -s "$expected" "$destination"
      printf 'fix: codex AGENTS.md symlink repointed from %s to %s\n' "$current" "$expected"
    else
      fail "$destination points to $current, not kit-managed; move it by hand"
    fi
    return
  fi
  if [[ -f "$destination" ]]; then
    if ! grep -Fxq "$HEADER" "$destination"; then
      fail "$destination is user-managed; move it before bootstrap"
    fi
    backup="$destination.bak.$(date +%Y%m%d-%H%M%S)"
    mv "$destination" "$backup"
    ln -s "$expected" "$destination"
    printf 'fix: kit AGENTS.md backed up to %s and symlinked\n' "$backup"
    return
  fi
  if [[ -e "$destination" ]]; then
    fail "$destination is not a file or symlink; remove it by hand"
  fi
  ln -s "$expected" "$destination"
  printf 'fix: codex AGENTS.md symlink created\n'
}

if [[ ! -e "$KIT" ]]; then
  if command -v gh >/dev/null 2>&1 && [[ "$SRC" == "https://github.com/$REPOSITORY" ]]; then
    gh repo clone "$REPOSITORY" "$KIT"
  else
    git clone "$SRC" "$KIT"
  fi
elif [[ ! -d "$KIT" ]]; then
  fail "$KIT exists and is not a directory"
fi

ensure_agents_link

if command -v devin >/dev/null 2>&1; then
  devin_plugins="$(devin plugins list 2>/dev/null || true)"
  if [[ "$devin_plugins" == *"agent-rules-kit"* || "$devin_plugins" == *"core"* ]]; then
    printf 'ok: devin plugin installed\n'
  elif devin plugins install "$REPOSITORY" -y >/dev/null 2>&1; then
    printf 'fix: devin plugin installed\n'
  else
    warn "devin plugin installation failed; sign in and retry"
  fi
fi

codex="$(codex_bin || true)"
if [[ -n "$codex" ]]; then
  marketplaces="$("$codex" plugin marketplace list 2>/dev/null || true)"
  if [[ "$marketplaces" == *"ai-kit"* ]]; then
    printf 'ok: codex marketplace ai-kit registered\n'
  elif "$codex" plugin marketplace add "$REPOSITORY" --ref main >/dev/null 2>&1; then
    printf 'fix: codex marketplace ai-kit registered\n'
  else
    warn "codex marketplace ai-kit registration failed; retry after authentication"
  fi

  plugins="$("$codex" plugin list 2>/dev/null || true)"
  for plugin_dir in "$KIT"/plugins/*/; do
    plugin_name="$(basename "$plugin_dir")"
    [[ -d "$plugin_dir/.devin-plugin" || -d "$plugin_dir/.claude-plugin" || -f "$plugin_dir/plugin.json" ]] || continue
    if [[ "$plugins" == *"$plugin_name@ai-kit"* ]]; then
      printf 'ok: codex plugin %s@ai-kit installed\n' "$plugin_name"
    elif "$codex" plugin add "$plugin_name@ai-kit" >/dev/null 2>&1; then
      printf 'fix: codex plugin %s@ai-kit installed\n' "$plugin_name"
    else
      warn "codex plugin $plugin_name@ai-kit installation failed; run: codex plugin add $plugin_name@ai-kit"
    fi
  done
fi

if command -v claude >/dev/null 2>&1; then
  claude_marketplaces="$(claude plugin marketplace list --json 2>/dev/null || true)"
  if json_contains "$claude_marketplaces" "ai-kit"; then
    printf 'ok: claude marketplace ai-kit registered\n'
  elif claude plugin marketplace add "$REPOSITORY" --json >/dev/null 2>&1; then
    printf 'fix: claude marketplace ai-kit registered\n'
  else
    warn "claude marketplace ai-kit registration failed; retry after authentication"
  fi

  claude_plugins="$(claude plugin list --json 2>/dev/null || true)"
  if json_contains "$claude_plugins" "all@ai-kit"; then
    printf 'ok: claude bundle all@ai-kit installed\n'
  elif claude plugin install all@ai-kit --json >/dev/null 2>&1; then
    printf 'fix: claude bundle all@ai-kit installed\n'
  else
    warn "claude bundle all@ai-kit installation failed; run: claude plugin install all@ai-kit"
  fi
fi

if [[ "${OSTYPE:-}" == darwin* && "${AI_KIT_NO_LAUNCHD:-0}" != "1" ]]; then
  launch_agents="$HOME/Library/LaunchAgents"
  destination="$launch_agents/ai-kit.refresh.plist"
  escaped_kit="${KIT//&/\\&}"
  escaped_kit="${escaped_kit//|/\\|}"
  # launchd does not expand ~, so the PATH entry for ~/.local/bin is rendered here (KIT-022)
  escaped_home="${HOME//&/\\&}"
  escaped_home="${escaped_home//|/\\|}"
  mkdir -p "$launch_agents"
  sed -e "s|@KIT@|$escaped_kit|g" -e "s|@HOME@|$escaped_home|g" \
    "$KIT/platforms/kits/launchd/ai-kit.refresh.plist" > "$destination"
  launchctl bootout "gui/$UID/ai-kit.refresh" 2>/dev/null || true
  launchctl bootstrap "gui/$UID" "$destination"
  printf 'fix: launchd refresh installed\n'
fi

exec "$KIT/platforms/tools/doctor.sh"
