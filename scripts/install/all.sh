#!/usr/bin/env bash
# Instala em todos os destinos e roda a validacao.
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
KIT_DIR="$(cd "$HERE/../.." && pwd)"

"$HERE/third-party.sh" --check
"$HERE/devin.sh"
"$HERE/cursor.sh"
"$HERE/windsurf.sh"
"$HERE/codex.sh"
"$KIT_DIR/scripts/check.sh"
