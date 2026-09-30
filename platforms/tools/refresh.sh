#!/usr/bin/env bash
# Atualiza o kit instalado. Uso: refresh.sh [--quiet]
# pull --ff-only; compara VERSION/LAYOUT_VERSION do repo com o estado instalado
# em ~/.config/agent-rules-kit/. LAYOUT diferente -> reinstalacao completa
# (--clean); so VERSION diferente -> reinstall; igual -> silencio com --quiet.
set -euo pipefail

KIT="$HOME/.ai-kit"
STATE="$HOME/.config/agent-rules-kit"
QUIET=0; [[ "${1:-}" == "--quiet" ]] && QUIET=1
say() { [[ $QUIET -eq 0 ]] && echo "$@" || true; }

[[ -d "$KIT" ]] || { say "refresh: $KIT nao existe; rode platforms/tools/bootstrap.sh"; exit 0; }

if ! git -C "$KIT" pull --ff-only -q 2>/dev/null; then
  say "refresh: AVISO: pull falhou (rede ou divergencia); usando estado local"
fi

repo_ver="$(cat "$KIT/VERSION" 2>/dev/null || echo 0)"
repo_layout="$(cat "$KIT/LAYOUT_VERSION" 2>/dev/null || echo 0)"
inst_ver="$(cat "$STATE/VERSION" 2>/dev/null || echo '')"
inst_layout="$(cat "$STATE/LAYOUT_VERSION" 2>/dev/null || echo '')"

if [[ "$repo_layout" != "$inst_layout" ]]; then
  say "refresh: layout $inst_layout -> $repo_layout; reinstalacao completa"
  exec "$KIT/platforms/install/all.sh" --clean
elif [[ "$repo_ver" != "$inst_ver" ]]; then
  say "refresh: versao $inst_ver -> $repo_ver; reinstalando"
  exec "$KIT/platforms/install/all.sh"
fi
exit 0
