#!/usr/bin/env bash
# Initializes docs/spec/ in a repo. Usage: init-spec.sh <repo-dir>
set -euo pipefail

KIT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
REPO="${1:?usage: init-spec.sh <repo-dir>}"

mkdir -p "$REPO/docs/spec/features" \
         "$REPO/docs/spec/requirements/functional" \
         "$REPO/docs/spec/requirements/non-functional" \
         "$REPO/docs/spec/decisions" \
         "$REPO/docs/spec/debts"

for d in features requirements/functional requirements/non-functional decisions debts; do
  touch "$REPO/docs/spec/$d/.gitkeep"
done

if [[ ! -f "$REPO/docs/spec/spec.md" ]]; then
  cp "$KIT_DIR/templates/spec-index.md" "$REPO/docs/spec/spec.md"
  echo "created docs/spec/spec.md (edit the frontmatter)"
else
  echo "docs/spec/spec.md already exists; not overwritten"
fi

"$KIT_DIR/platforms/tools/sync-project.sh" "$REPO"

echo "Next step: /sdd-constitution in the target repo"
