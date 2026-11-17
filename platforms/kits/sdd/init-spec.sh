#!/usr/bin/env bash
# Initializes docs/spec/ in a repo, spec.md with the sdd: parameters included. Usage: init-spec.sh <repo-dir>
# Precondition: the repo must already have AGENTS.md (the sync generates CLAUDE.md importing it).
set -euo pipefail

KIT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
REPO="${1:?usage: init-spec.sh <repo-dir>}"

# The profile's project.kind picks the template and the folders (KIT-089, KIT-100); an invalid profile stops here.
KIND=$(python3 "$KIT_DIR/platforms/tools/profile.py" resolve --section project --json "$REPO" \
  | sed -n 's/^ *"kind": "\([a-z]*\)".*/\1/p')

# tooling runs the FEAT-only flow: no NEED and no REQ folder.
FOLDERS="needs features requirements/functional requirements/non-functional decisions debts"
if [[ "$KIND" == tooling ]]; then
  FOLDERS="features decisions debts"
fi
for d in $FOLDERS; do
  mkdir -p "$REPO/docs/spec/$d"
  touch "$REPO/docs/spec/$d/.gitkeep"
done

# The business and game templates carry the sdd: process parameters (KIT-067); /sdd-constitution sets them. The
# tooling one carries none, since a block there would hide the tooling preset (KIT-100).
if [[ ! -f "$REPO/docs/spec/spec.md" ]]; then
  TEMPLATE="spec-index-business.md"
  NOTE="with the sdd: parameters at the kit defaults (edit the frontmatter)"
  if [[ "$KIND" == game ]]; then
    TEMPLATE="spec-index-game.md"
  elif [[ "$KIND" == tooling ]]; then
    TEMPLATE="spec-index-tooling.md"
    NOTE="with no sdd: block (the tooling preset of .ai-kit.yaml applies)"
  fi
  cp "$KIT_DIR/plugins/guardrails/templates/$TEMPLATE" "$REPO/docs/spec/spec.md"
  echo "created docs/spec/spec.md from $TEMPLATE (project.kind: ${KIND:-business}) $NOTE"
else
  echo "docs/spec/spec.md already exists; not overwritten"
  grep -q '^sdd:' "$REPO/docs/spec/spec.md" \
    || echo "docs/spec/spec.md has no sdd: block, so every parameter takes its kit default; /sdd-constitution writes it"
fi

[[ -f "$REPO/AGENTS.md" ]] || { echo "init-spec: $REPO/AGENTS.md missing; create it from plugins/guardrails/templates/project-agents-*.md first"; exit 1; }

"$KIT_DIR/platforms/tools/sync-project.sh" "$REPO"

echo "Next step: /sdd-constitution in the target repo"
