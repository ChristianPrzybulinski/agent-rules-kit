#!/usr/bin/env bash
# Kit validation. Usage:
#   check.sh              validates layout, frontmatters, indexes, links, lock, duplication
#   check.sh --spec <dir> validates a docs/spec directory against the schemas
#   check.sh --links      includes absolute ~/.ai-kit/... links in the check
set -euo pipefail

KIT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

if [[ "${1:-}" == "--spec" ]]; then
  exec python3 "$KIT_DIR/platforms/ci/validations/check_spec.py" "${2:?usage: check.sh --spec <dir>}" "$KIT_DIR/platforms/ci/schemas"
fi

exec python3 "$KIT_DIR/platforms/ci/validations/check_kit.py" "$@"
