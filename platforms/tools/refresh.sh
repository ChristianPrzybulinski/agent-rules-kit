#!/usr/bin/env bash
# Updates the kit clone and Codex marketplace plugin. Usage: refresh.sh
set -euo pipefail

KIT="${AI_KIT_DIR:-$HOME/.ai-kit}"

warn() {
  printf 'WARN: refresh: %s\n' "$*" >&2
}

fail() {
  printf 'FAIL: refresh: %s\n' "$*" >&2
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

run_step "git pull --ff-only failed" git -C "$KIT" pull --ff-only

codex="$(codex_bin || true)"
if [[ -n "$codex" ]]; then
  marketplaces="$("$codex" plugin marketplace list 2>/dev/null || true)"
  if [[ "$marketplaces" == *"ai-kit"* ]]; then
    run_step "codex marketplace upgrade failed" "$codex" plugin marketplace upgrade ai-kit
  else
    warn "codex marketplace ai-kit not registered — run platforms/tools/bootstrap.sh"
  fi
fi

sha="$(git -C "$KIT" rev-parse --short HEAD)" || fail "cannot read HEAD"
date="$(git -C "$KIT" show -s --format=%cs HEAD)" || fail "cannot read commit date"
printf 'refresh: %s %s main\n' "$sha" "$date"
