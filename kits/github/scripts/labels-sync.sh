#!/usr/bin/env bash
# Aplica os labels de labels.json no repo atual (ou no repo passado como $1).
# Idempotente: gh label create --force atualiza labels existentes.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LABELS="${LABELS_JSON:-$HERE/labels.json}"
REPO="${1:-}"

command -v gh >/dev/null || { echo "gh nao encontrado" >&2; exit 1; }
command -v python3 >/dev/null || { echo "python3 nao encontrado" >&2; exit 1; }

args=()
[[ -n "$REPO" ]] && args=(-R "$REPO")

python3 - "$LABELS" <<'PY' | while IFS='|' read -r name color desc; do
import json, sys
for l in json.load(open(sys.argv[1])):
    print("|".join([l["name"], l["color"], l.get("description", "")]))
PY
  gh label create "$name" --color "$color" --description "$desc" --force "${args[@]}"
done
echo "labels sincronizados"
