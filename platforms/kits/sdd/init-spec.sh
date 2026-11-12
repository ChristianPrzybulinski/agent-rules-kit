#!/usr/bin/env bash
# Initializes docs/spec/ in a repo. Usage: init-spec.sh <repo-dir>
# Precondition: the repo must already have AGENTS.md (the sync generates CLAUDE.md importing it).
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
  cp "$KIT_DIR/plugins/sdd/templates/spec-index.md" "$REPO/docs/spec/spec.md"
  echo "created docs/spec/spec.md (edit the frontmatter)"
else
  echo "docs/spec/spec.md already exists; not overwritten"
fi

[[ -f "$REPO/AGENTS.md" ]] || { echo "init-spec: $REPO/AGENTS.md missing; create it from plugins/dev-*/templates/project-agents-*.md first"; exit 1; }

"$KIT_DIR/platforms/tools/sync-project.sh" "$REPO"

echo "Next step: /sdd-constitution in the target repo"
