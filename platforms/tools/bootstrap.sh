#!/usr/bin/env bash
# Installs the plugin-first kit on this machine. Usage: bootstrap.sh
set -euo pipefail

KIT="${AI_KIT_DIR:-$HOME/.ai-kit}"
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

codex_bin() {
  local candidate
  [[ "${AI_KIT_NO_CODEX_CLI:-0}" != "1" ]] || return 1
  candidate="$(command -v codex 2>/dev/null || true)"
  if [[ -n "$candidate" && -x "$candidate" ]]; then
    printf '%s\n' "$candidate"
    return 0
  fi
  for candidate in \
    /Applications/ChatGPT.app/Contents/Resources/codex-cli/bin/codex \
    /Applications/Codex.app/Contents/Resources/codex-cli/bin/codex; do
    if [[ -x "$candidate" ]]; then
      printf '%s\n' "$candidate"
      return 0
    fi
  done
  candidate="$(find "$HOME/.cache/codex-runtimes" /Applications/ChatGPT.app /Applications/Codex.app \
    -type f -name codex -perm -u+x 2>/dev/null | head -1 || true)"
  if [[ -n "$candidate" && -x "$candidate" ]]; then
    printf '%s\n' "$candidate"
    return 0
  fi
  return 1
}

ensure_agents_link() {
  local destination="$HOME/.codex/AGENTS.md"
  local expected="$KIT/AGENTS.md"
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
      printf 'fix: codex AGENTS.md symlink repaired\n'
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
  if [[ "$devin_plugins" == *"ai-kit"* ]]; then
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
  if [[ "$plugins" == *"ai-kit@ai-kit"* ]]; then
    printf 'ok: codex plugin ai-kit@ai-kit installed\n'
  elif "$codex" plugin add ai-kit@ai-kit >/dev/null 2>&1; then
    printf 'fix: codex plugin ai-kit@ai-kit installed\n'
  else
    warn "codex plugin ai-kit@ai-kit installation failed; run: codex plugin add ai-kit@ai-kit"
  fi
fi

if [[ "${OSTYPE:-}" == darwin* && "${AI_KIT_NO_LAUNCHD:-0}" != "1" ]]; then
  launch_agents="$HOME/Library/LaunchAgents"
  destination="$launch_agents/ai-kit.refresh.plist"
  escaped_kit="${KIT//&/\\&}"
  escaped_kit="${escaped_kit//|/\\|}"
  mkdir -p "$launch_agents"
  sed "s|@KIT@|$escaped_kit|g" "$KIT/platforms/kits/launchd/ai-kit.refresh.plist" > "$destination"
  launchctl bootout "gui/$UID/ai-kit.refresh" 2>/dev/null || true
  launchctl bootstrap "gui/$UID" "$destination"
  printf 'fix: launchd refresh installed\n'
fi

exec "$KIT/platforms/tools/doctor.sh"
