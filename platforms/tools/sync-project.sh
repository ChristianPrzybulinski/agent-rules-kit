#!/usr/bin/env bash
# Sincroniza o validador de specs com um projeto (copia, sem link com o kit).
# Uso: sync-project.sh <repo-dir>           instala/atualiza .github/spec-lint/
#      sync-project.sh --check <repo-dir>   compara com o kit; exit 1 se divergir
set -euo pipefail

KIT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

MODE="install"
if [[ "${1:-}" == "--check" ]]; then MODE="check"; shift; fi
REPO="${1:?uso: sync-project.sh [--check] <repo-dir>}"
DEST="$REPO/.github/spec-lint"
SCHEMAS="spec feature requirement decision debt"

hash_file() { shasum -a 256 "$1" | cut -d' ' -f1; }

kit_files() { # imprime "src rel-dest"
  echo "$KIT_DIR/platforms/ci/validations/check_spec.py check_spec.py"
  for s in $SCHEMAS; do
    echo "$KIT_DIR/platforms/ci/schemas/$s.schema.json schemas/$s.schema.json"
  done
}

if [[ "$MODE" == check ]]; then
  FAILED=0
  expected="$(cat "$KIT_DIR/VERSION")"
  actual="$(cat "$DEST/KIT_VERSION" 2>/dev/null || echo '')"
  [[ "$actual" == "$expected" ]] || { echo "sync: $REPO KIT_VERSION='$actual' kit='$expected'"; FAILED=1; }
  kit_files | while read -r src rel; do
    dst="$DEST/$rel"
    if [[ ! -f "$dst" ]]; then echo "sync: $dst ausente"; exit 1; fi
    [[ "$(hash_file "$src")" == "$(hash_file "$dst")" ]] || { echo "sync: $rel diverge do kit"; exit 1; }
  done || FAILED=1
  [[ -f "$REPO/.github/workflows/spec-lint.yml" ]] || { echo "sync: spec-lint.yml ausente"; FAILED=1; }
  if [[ $FAILED -eq 0 ]]; then echo "sync: $REPO consistente com kit $expected"; else exit 1; fi
  exit 0
fi

mkdir -p "$DEST/schemas"
kit_files | while read -r src rel; do cp "$src" "$DEST/$rel"; done
cat "$KIT_DIR/VERSION" > "$DEST/KIT_VERSION"
mkdir -p "$REPO/.github/workflows"
cp "$KIT_DIR/platforms/kits/github/workflows/spec-lint.yml" "$REPO/.github/workflows/spec-lint.yml"
cat > "$DEST/README.md" <<EOF
# spec-lint/ — cópia gerada

Gerada por \`platforms/tools/sync-project.sh\` do agent-rules-kit v$(cat "$KIT_DIR/VERSION").
Não editar — atualizar rodando o sync novamente. \`KIT_VERSION\` registra a versão de origem.
EOF
echo "sync: $REPO/.github/spec-lint <- kit $(cat "$KIT_DIR/VERSION")"
