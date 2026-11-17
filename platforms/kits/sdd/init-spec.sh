#!/usr/bin/env bash
# Initializes docs/spec/ in a repo: the folders of the profile's sdd.flow and the spec.md template of its
# project.kind (none carries an sdd: block, KIT-087 P4). Usage: init-spec.sh <repo-dir>
# Precondition: the repo must already have AGENTS.md (the sync generates CLAUDE.md importing it).
set -euo pipefail

KIT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
REPO="${1:?usage: init-spec.sh <repo-dir>}"

# The profile's project.kind picks the template (KIT-089) and its resolved sdd.flow the folders (KIT-100), so a kind
# overridden by an explicit flow still gets its flow's folders; an invalid profile stops here.
KIND=$(python3 "$KIT_DIR/platforms/tools/profile.py" resolve --section project --json "$REPO" \
  | sed -n 's/^ *"kind": "\([a-z]*\)".*/\1/p')
FLOW=$(python3 "$KIT_DIR/platforms/tools/profile.py" resolve --section sdd --json "$REPO" 2>/dev/null \
  | sed -n 's/^ *"flow": "\([a-z-]*\)".*/\1/p')

# The FEAT-only flow keeps no NEED and no REQ folder.
FOLDERS="needs features requirements/functional requirements/non-functional decisions debts"
if [[ "$FLOW" == feat-only ]]; then
  FOLDERS="features decisions debts"
fi
for d in $FOLDERS; do
  mkdir -p "$REPO/docs/spec/$d"
  touch "$REPO/docs/spec/$d/.gitkeep"
done

# No template carries an sdd: block (KIT-087 P4): the process parameters are the sdd section of .ai-kit.yaml, which
# /sdd-constitution writes; a key left out takes its project.kind preset or default.
if [[ ! -f "$REPO/docs/spec/spec.md" ]]; then
  TEMPLATE="spec-index-business.md"
  NOTE="(the process parameters go in the sdd section of .ai-kit.yaml)"
  if [[ "$KIND" == game ]]; then
    TEMPLATE="spec-index-game.md"
  elif [[ "$KIND" == tooling ]]; then
    TEMPLATE="spec-index-tooling.md"
  fi
  cp "$KIT_DIR/plugins/guardrails/templates/$TEMPLATE" "$REPO/docs/spec/spec.md"
  echo "created docs/spec/spec.md from $TEMPLATE (project.kind: ${KIND:-business}) $NOTE"
else
  echo "docs/spec/spec.md already exists; not overwritten"
  if grep -q '^sdd:' "$REPO/docs/spec/spec.md"; then
    echo "docs/spec/spec.md still holds an sdd: block, which the kit no longer reads (KIT-087 P4): move its keys under sdd: in .ai-kit.yaml"
  fi
fi

[[ -f "$REPO/AGENTS.md" ]] || { echo "init-spec: $REPO/AGENTS.md missing; create it from plugins/guardrails/templates/project-agents-*.md first"; exit 1; }

"$KIT_DIR/platforms/tools/sync-project.sh" "$REPO"

echo "Next step: /sdd-constitution in the target repo"
