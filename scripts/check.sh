#!/usr/bin/env bash
# Validacao do kit. Uso:
#   check.sh              valida regras, skills, tamanhos, schemas e .mdc gerados
#   check.sh --spec <dir> valida um diretorio docs/spec contra os schemas
set -euo pipefail

KIT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
FAILED=0
fail() { echo "FALHA: $*" >&2; FAILED=1; }

if [[ "${1:-}" == "--spec" ]]; then
  exec python3 "$KIT_DIR/scripts/check_spec.py" "${2:?uso: check.sh --spec <dir>}" "$KIT_DIR/schemas"
fi

YAML_OK=0
python3 -c "import yaml" 2>/dev/null && YAML_OK=1 || \
  echo "AVISO: PyYAML nao disponivel; validacao de frontmatter sera estrutural." >&2

check_frontmatter() { # $1 arquivo, $2 basename de pasta esperado (vazio = nao checa)
  local f="$1" expect="${2:-}"
  [[ "$(head -1 "$f")" == "---" ]] || { fail "$f: frontmatter nao comeca com --- na linha 1"; return; }
  local close
  close="$(awk 'NR>1 && $0=="---" {print NR; exit}' "$f")"
  [[ -n "$close" ]] || { fail "$f: frontmatter sem fechamento ---"; return; }
  awk -v c="$close" 'NR>1 && NR<c && /^description:[[:space:]]*[^[:space:]]/ {ok=1} END{exit !ok}' "$f" \
    || fail "$f: frontmatter sem description:"
  if [[ -n "$expect" ]]; then
    local name
    name="$(awk -v c="$close" 'NR>1 && NR<c && /^name:[[:space:]]*/ {sub(/^name:[[:space:]]*/,""); gsub(/["'"'"']/,""); print; exit}' "$f")"
    [[ "$name" == "$expect" ]] || fail "$f: name='$name' != pasta '$expect'"
  fi
  if [[ "$YAML_OK" == 1 ]]; then
    python3 - "$f" "$close" <<'PY' || fail "$f: YAML invalido"
import sys, yaml
f, close = sys.argv[1], int(sys.argv[2])
yaml.safe_load("\n".join(open(f).read().splitlines()[1:close-1]))
PY
  else
    awk -v c="$close" 'NR>1 && NR<c && $0 !~ /^([[:space:]]*-[[:space:]]|[[:space:]]*[A-Za-z_-]+:|$)/ {bad=1} END{exit bad}' "$f" \
      || fail "$f: frontmatter com estrutura suspeita (sem PyYAML)"
  fi
}

# regras (recursivo)
while IFS= read -r f; do check_frontmatter "$f"; done < <(find "$KIT_DIR/rules" -name '*.md')

# skills + processes: basename unico e name == basename
seen_file="$(mktemp)"
trap 'rm -f "$seen_file"' EXIT
while IFS= read -r f; do
  dir="$(basename "$(dirname "$f")")"
  if grep -q "^$dir$" "$seen_file"; then
    fail "basename duplicado de skill: '$dir' em $f"
  else
    echo "$dir" >> "$seen_file"
  fi
  check_frontmatter "$f" "$dir"
done < <(find "$KIT_DIR/skills" "$KIT_DIR/processes" -name SKILL.md)

# tamanhos
n=$(wc -l < "$KIT_DIR/AGENTS.md")
(( n <= 150 )) || fail "AGENTS.md tem $n linhas (>150)"
for f in "$KIT_DIR"/templates/projects/*/AGENTS.md; do
  [[ -e "$f" ]] || continue
  n=$(wc -l < "$f")
  (( n <= 150 )) || fail "$f tem $n linhas (>150)"
done

chars="$(awk 'p{print} $0=="---"{p=1}' "$KIT_DIR/prompts/chatgpt-compact.md" | wc -m | tr -d ' ')"
(( chars <= 1500 )) || fail "prompts/chatgpt-compact.md (apos ---): $chars chars (>1500)"

# schemas sao JSON valido
for f in "$KIT_DIR"/schemas/*.schema.json; do
  [[ -e "$f" ]] || continue
  python3 -c "import json,sys; json.load(open(sys.argv[1]))" "$f" || fail "$f: JSON invalido"
done

# .mdc gerados
if [[ -d "$HOME/.cursor/rules" ]]; then
  for f in "$HOME"/.cursor/rules/*.mdc; do
    [[ -e "$f" ]] || continue
    [[ "$(grep -c '^---$' "$f")" == 2 ]] || fail "$f: numero de linhas --- != 2"
    ! grep -q '^trigger:' "$f" || fail "$f: ainda contem trigger:"
  done
fi

[[ $FAILED -eq 0 ]] && echo "check: OK" || { echo "check: falhou" >&2; exit 1; }
