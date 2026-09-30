#!/usr/bin/env bash
# Inicializa docs/spec/ num repo. Uso: init-spec.sh <repo-dir>
set -euo pipefail

KIT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
REPO="${1:?uso: init-spec.sh <repo-dir>}"

mkdir -p "$REPO/docs/spec/features" \
         "$REPO/docs/spec/requirements/functional" \
         "$REPO/docs/spec/requirements/non-functional" \
         "$REPO/docs/spec/decisions" \
         "$REPO/docs/spec/debts"

for d in features requirements/functional requirements/non-functional decisions debts; do
  touch "$REPO/docs/spec/$d/.gitkeep"
done

if [[ ! -f "$REPO/docs/spec/spec.md" ]]; then
  cp "$KIT_DIR/agents/templates/spec-index.md" "$REPO/docs/spec/spec.md"
  echo "criado docs/spec/spec.md (edite o frontmatter)"
else
  echo "docs/spec/spec.md ja existe; nao sobrescrito"
fi

"$KIT_DIR/platforms/tools/sync-project.sh" "$REPO"

echo "Proximo passo: /sdd-constitution no repo alvo"
