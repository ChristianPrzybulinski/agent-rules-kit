#!/usr/bin/env bash
# Validacao do kit. Uso:
#   check.sh              valida layout, frontmatters, indices, links, lock, duplicacao
#   check.sh --spec <dir> valida um diretorio docs/spec contra os schemas
#   check.sh --links      inclui links absolutos ~/.ai-kit/... na checagem
set -euo pipefail

KIT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

if [[ "${1:-}" == "--spec" ]]; then
  exec python3 "$KIT_DIR/platforms/ci/validations/check_spec.py" "${2:?uso: check.sh --spec <dir>}" "$KIT_DIR/platforms/ci/schemas"
fi

exec python3 "$KIT_DIR/platforms/ci/validations/check_kit.py" "$@"
