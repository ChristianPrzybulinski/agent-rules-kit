#!/usr/bin/env bash
# Syncs the spec validator with a project (a copy, no link to the kit).
# Usage: sync-project.sh [--workflow <file>] <repo-dir>           installs/updates .github/spec-lint/
#        sync-project.sh --check [--workflow <file>] <repo-dir>   compares with the kit and scans the
#                                                                repo's *.md for obsolete kit paths;
#                                                                exit 1 on any divergence or stale citation
# --workflow names the CI file that must run check_spec.py. Without it, --check
# accepts any file under .github/workflows/ containing check_spec.py, and install
# copies the kit workflow (as spec-lint.yml) only if the project has none.
set -euo pipefail

KIT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

MODE="install"
WORKFLOW=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --check) MODE="check" ;;
    --workflow) WORKFLOW="${2:?usage: sync-project.sh [--check] [--workflow <file>] <repo-dir>}"; shift ;;
    --) shift; break ;;
    *) break ;;
  esac
  shift
done
REPO="${1:?usage: sync-project.sh [--check] [--workflow <file>] <repo-dir>}"
DEST="$REPO/.github/spec-lint"
SCHEMAS="spec feature requirement decision debt"

if [[ -n "$WORKFLOW" && ( "$WORKFLOW" == */* || "$WORKFLOW" == .* ) ]]; then
  echo "sync: --workflow must be a plain file name under .github/workflows/" >&2
  exit 2
fi

hash_file() { shasum -a 256 "$1" | cut -d' ' -f1; }

kit_files() { # prints "src rel-dest"
  echo "$KIT_DIR/platforms/ci/validations/check_spec.py check_spec.py"
  for s in $SCHEMAS; do
    echo "$KIT_DIR/platforms/ci/schemas/$s.schema.json schemas/$s.schema.json"
  done
  # Journeys are opt-in: only a project with docs/spec/journeys gets the journey schema and the
  # traceability validator.
  if [[ -d "$REPO/docs/spec/journeys" ]]; then
    echo "$KIT_DIR/platforms/ci/schemas/journey.schema.json schemas/journey.schema.json"
    echo "$KIT_DIR/platforms/ci/validations/spec_trace.py spec_trace.py"
  fi
}

has_check_spec_workflow() { # any project workflow that runs check_spec.py
  local wf
  for wf in "$REPO"/.github/workflows/*; do
    [[ -f "$wf" ]] && grep -q "check_spec\.py" "$wf" && return 0
  done
  return 1
}

# Obsolete kit paths (layouts 1.x to 9.x). A consumer line that must keep one
# (historical citation) appends the marker "<!-- kit-path-ok -->".
# .claude/ is skipped: generated kit copies there are verified by their own
# manifest and repo-owned content under .claude/ is not a kit citation.
STALE_KIT_PATHS='agents/skills/|agents/rules/|agents/knowledge/|rules/godot/|rules/java/|rules/git/|kits/java-maven/|kits/github/|platforms/install/|knowledge/|processes/sdd/|plugins/ai-kit/'
STALE_OPT_OUT='<!-- kit-path-ok -->'

scan_stale_kit_paths() { # $1 = repo dir; prints one line per stale citation; returns 1 if any
  local hits
  hits="$(grep -rnE --include='*.md' --exclude-dir=.git --exclude-dir=node_modules --exclude-dir=.claude \
      "(^|[^/A-Za-z0-9_.-])($STALE_KIT_PATHS)" "$1" 2>/dev/null \
    | sed "s|^${1%/}/||" \
    | grep -vE '^([^:]*/)?(legacy|docs/sessions)/' \
    | grep -vF -- "$STALE_OPT_OUT" || true)"
  [[ -n "$hits" ]] || return 0
  printf '%s\n' "$hits" | sed 's|^|sync: stale kit path: |'
  echo "sync: the 10.x layout is frozen (docs/design.md, Layout stability); fix the citation or append $STALE_OPT_OUT"
  return 1
}

if [[ "$MODE" == check ]]; then
  FAILED=0
  expected="$(cat "$KIT_DIR/VERSION")"
  actual="$(cat "$DEST/KIT_VERSION" 2>/dev/null || echo '')"
  [[ "$actual" == "$expected" ]] || { echo "sync: $REPO KIT_VERSION='$actual' kit='$expected'"; FAILED=1; }
  kit_files | while read -r src rel; do
    dst="$DEST/$rel"
    if [[ ! -f "$dst" ]]; then echo "sync: $dst missing"; exit 1; fi
    [[ "$(hash_file "$src")" == "$(hash_file "$dst")" ]] || { echo "sync: $rel diverges from the kit"; exit 1; }
  done || FAILED=1
  if [[ -n "$WORKFLOW" ]]; then
    wf="$REPO/.github/workflows/$WORKFLOW"
    if [[ ! -f "$wf" ]]; then
      echo "sync: $WORKFLOW missing"; FAILED=1
    elif ! grep -q "check_spec\.py" "$wf"; then
      echo "sync: $WORKFLOW does not run check_spec.py"; FAILED=1
    fi
  elif ! has_check_spec_workflow; then
    echo "sync: no workflow under .github/workflows runs check_spec.py"; FAILED=1
  fi
  scan_stale_kit_paths "$REPO" || FAILED=1
  if [[ $FAILED -eq 0 ]]; then echo "sync: $REPO consistent with kit $expected"; else exit 1; fi
  exit 0
fi

mkdir -p "$DEST/schemas"
kit_files | while read -r src rel; do cp "$src" "$DEST/$rel"; done
cat "$KIT_DIR/VERSION" > "$DEST/KIT_VERSION"
mkdir -p "$REPO/.github/workflows"
if has_check_spec_workflow; then
  echo "sync: $REPO already runs check_spec.py in CI; kit workflow not copied"
else
  wf="$REPO/.github/workflows/${WORKFLOW:-spec-lint.yml}"
  [[ ! -f "$wf" ]] || { echo "sync: $wf exists and does not run check_spec.py; not overwriting" >&2; exit 1; }
  cp "$KIT_DIR/platforms/kits/github/workflows/spec-lint.yml" "$wf"
fi
cat > "$DEST/README.md" <<EOF
# spec-lint/ — generated copy

Generated by \`platforms/tools/sync-project.sh\` from agent-rules-kit v$(cat "$KIT_DIR/VERSION").
Do not edit — update by running the sync again. \`KIT_VERSION\` records the source version.
EOF
echo "sync: $REPO/.github/spec-lint <- kit $(cat "$KIT_DIR/VERSION")"
