#!/usr/bin/env bash
# Applies the labels.json labels to the current repo (or the repo passed as $1).
# Idempotent: gh label create --force updates existing labels.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LABELS="${LABELS_JSON:-$HERE/labels.json}"
REPO="${1:-}"

command -v gh >/dev/null || { echo "gh not found" >&2; exit 1; }
command -v python3 >/dev/null || { echo "python3 not found" >&2; exit 1; }

args=()
[[ -n "$REPO" ]] && args=(-R "$REPO")

python3 - "$LABELS" <<'PY' | while IFS='|' read -r name color desc; do
import json, sys
for l in json.load(open(sys.argv[1])):
    print("|".join([l["name"], l["color"], l.get("description", "")]))
PY
  gh label create "$name" --color "$color" --description "$desc" --force "${args[@]}"
done
echo "labels synced"
