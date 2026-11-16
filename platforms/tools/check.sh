#!/usr/bin/env bash
# Kit validation. Usage:
#   check.sh              validates kit invariants, generated plugin INDEX.md files and Claude manifests
#   check.sh --spec <dir> validates a docs/spec directory against the schemas
#   check.sh --links      includes absolute ~/.ai-kit/... links in the check
#   check.sh --tests [run_tests.py arguments]
#                         runs the kit's tests through platforms/tools/run_tests.py, the entry CI's jobs use (KIT-077);
#                         the TDD loop: check.sh --tests --layer unit,contract, or the test modules you changed
set -euo pipefail

KIT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

if [[ "${1:-}" == "--spec" ]]; then
  exec python3 "$KIT_DIR/platforms/ci/validations/check_spec.py" "${2:?usage: check.sh --spec <dir>}" "$KIT_DIR/platforms/ci/schemas"
fi

if [[ "${1:-}" == "--tests" ]]; then
  shift
  exec python3 -B "$KIT_DIR/platforms/tools/run_tests.py" "$@"
fi

python3 "$KIT_DIR/platforms/ci/validations/check_kit.py" "$@"

# plugin INDEX.md files are generated (KIT-040); a stale one fails here and the message names the fix
python3 "$KIT_DIR/platforms/tools/gen_index.py" --check

if command -v claude >/dev/null 2>&1; then
  for plugin_dir in "$KIT_DIR"/plugins/*/; do
    [[ -d "$plugin_dir/.claude-plugin" ]] || continue
    claude plugin validate "$plugin_dir"
  done
  claude plugin validate "$KIT_DIR"
else
  printf 'check: claude plugin validate skipped (claude not in PATH)\n'
fi
