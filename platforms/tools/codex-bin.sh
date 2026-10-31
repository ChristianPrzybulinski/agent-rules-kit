#!/usr/bin/env bash
# Finds the Codex CLI for bootstrap.sh, refresh.sh and doctor.sh, which source this file (KIT-023).
# Usage: codex-bin.sh   prints the CLI the kit would use; exit 1 when there is none

# Lookup order: $CODEX_BIN, codex on PATH, the CLI bundled in ChatGPT.app or Codex.app, then any
# executable named codex under ~/.cache/codex-runtimes or the two apps. AI_KIT_NO_CODEX_CLI=1 finds none.
codex_bin() {
  local candidate
  [[ "${AI_KIT_NO_CODEX_CLI:-0}" != "1" ]] || return 1
  if [[ -n "${CODEX_BIN:-}" ]]; then
    if [[ -x "$CODEX_BIN" ]]; then
      printf '%s\n' "$CODEX_BIN"
      return 0
    fi
    printf 'WARN: CODEX_BIN=%s is not an executable file\n' "$CODEX_BIN" >&2
    return 1
  fi
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

if [[ "${BASH_SOURCE[0]}" == "$0" ]]; then
  codex_bin
fi
