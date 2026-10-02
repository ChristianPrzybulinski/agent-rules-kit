#!/usr/bin/env bash
# Kit validation. Usage:
#   check.sh              validates kit invariants and Claude plugin/marketplace manifests
#   check.sh --spec <dir> validates a docs/spec directory against the schemas
#   check.sh --links      includes absolute ~/.ai-kit/... links in the check
set -euo pipefail

KIT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

if [[ "${1:-}" == "--spec" ]]; then
  exec python3 "$KIT_DIR/platforms/ci/validations/check_spec.py" "${2:?usage: check.sh --spec <dir>}" "$KIT_DIR/platforms/ci/schemas"
fi

python3 "$KIT_DIR/platforms/ci/validations/check_kit.py" "$@"

if command -v claude >/dev/null 2>&1; then
  claude plugin validate "$KIT_DIR/plugins/ai-kit"
  claude plugin validate "$KIT_DIR"
else
  printf 'check: claude plugin validate skipped (claude not in PATH)\n'
fi
