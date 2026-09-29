#!/usr/bin/env bash
# Instala o kit de regras em Devin, Windsurf, Cursor e Claude Code.
# Uso: install.sh           instala em Devin, Windsurf e Cursor
#      install.sh --claude  tambem instala ~/.claude/CLAUDE.md (ATENCAO: Devin le esse arquivo
#                           como regra global -> texto duplicado no contexto; use so se usa Claude Code)
#      install.sh --check   so valida frontmatter e tamanhos
set -euo pipefail

KIT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MODE="install"; WITH_CLAUDE=0
for a in "$@"; do
  case "$a" in
    --check)  MODE="check" ;;
    --claude) WITH_CLAUDE=1 ;;
    *) echo "arg desconhecido: $a" >&2; exit 2 ;;
  esac
done

fail() { echo "FALHA: $*" >&2; FAILED=1; }
FAILED=0

check_frontmatter() { # $1 = arquivo, $2 = nome de pasta esperado (vazio = nao checa name)
  local f="$1" expect_name="${2:-}"
  [[ "$(head -1 "$f")" == "---" ]] || { fail "$f: frontmatter nao comeca com --- na linha 1"; return; }
  local close
  close="$(awk 'NR>1 && $0=="---" {print NR; exit}' "$f")"
  [[ -n "$close" ]] || { fail "$f: frontmatter sem fechamento ---"; return; }
  awk -v c="$close" 'NR>1 && NR<c && /^description:[[:space:]]*[^[:space:]]/ {ok=1} END{exit !ok}' "$f" \
    || fail "$f: frontmatter sem description:"
  if [[ -n "$expect_name" ]]; then
    local name
    name="$(awk -v c="$close" 'NR>1 && NR<c && /^name:[[:space:]]*/ {sub(/^name:[[:space:]]*/,""); gsub(/["'"'"']/,""); print; exit}' "$f")"
    [[ "$name" == "$expect_name" ]] || fail "$f: name='$name' != pasta '$expect_name'"
  fi
  if [[ "$YAML_OK" == 1 ]]; then
    python3 - "$f" "$close" <<'PY' || fail "$f: YAML invalido"
import sys, yaml
f, close = sys.argv[1], int(sys.argv[2])
lines = open(f).read().splitlines()
yaml.safe_load("\n".join(lines[1:close-1]))
PY
  else
    awk -v c="$close" 'NR>1 && NR<c && $0 !~ /^([[:space:]]*-[[:space:]]|[[:space:]]*[A-Za-z_-]+:|$)/ {bad=1} END{exit bad}' "$f" \
      || fail "$f: frontmatter com estrutura suspeita (sem PyYAML para validar)"
  fi
}

validate() {
  local f
  for f in "$KIT_DIR"/rules/*.md; do check_frontmatter "$f"; done
  for d in "$KIT_DIR"/skills/*/; do check_frontmatter "$d/SKILL.md" "$(basename "$d")"; done

  local n
  n=$(wc -l < "$KIT_DIR/AGENTS.md")
  (( n <= 150 )) || fail "AGENTS.md tem $n linhas (>150)"
  for f in "$KIT_DIR"/templates/*/AGENTS.md; do
    n=$(wc -l < "$f")
    (( n <= 150 )) || fail "$f tem $n linhas (>150)"
  done

  local chars
  chars="$(awk 'p{print} $0=="---"{p=1}' "$KIT_DIR/PROMPT-compact.md" | wc -m | tr -d ' ')"
  (( chars <= 1500 )) || fail "PROMPT-compact.md (apos ---): $chars chars (>1500)"

  if [[ -d "$HOME/.cursor/rules" ]]; then
    for f in "$HOME"/.cursor/rules/*.mdc; do
      [[ -e "$f" ]] || continue
      [[ "$(grep -c '^---$' "$f")" == 2 ]] || fail "$f: numero de linhas --- != 2"
      ! grep -q '^trigger:' "$f" || fail "$f: ainda contem trigger:"
    done
  fi
}

YAML_OK=0
python3 -c "import yaml" 2>/dev/null && YAML_OK=1 || \
  echo "AVISO: PyYAML nao disponivel; validacao de frontmatter sera estrutural."

if [[ "$MODE" == check ]]; then
  validate
  [[ $FAILED -eq 0 ]] && echo "check: OK" || { echo "check: falhou"; exit 1; }
  exit 0
fi

# --- instalacao ---
mkdir -p "$HOME/.config/devin/skills" "$HOME/.devin/rules" \
         "$HOME/.codeium/windsurf/memories" "$HOME/.cursor/rules"

cp "$KIT_DIR/AGENTS.md" "$HOME/.config/devin/AGENTS.md"
rsync -a --delete "$KIT_DIR/rules/"  "$HOME/.devin/rules/"
rsync -a --delete "$KIT_DIR/skills/" "$HOME/.config/devin/skills/"
cp "$KIT_DIR/AGENTS.md" "$HOME/.codeium/windsurf/memories/global_rules.md"
"$KIT_DIR/scripts/to-mdc.sh" "$HOME/.cursor/rules"
if [[ $WITH_CLAUDE -eq 1 ]]; then
  mkdir -p "$HOME/.claude" && cp "$KIT_DIR/AGENTS.md" "$HOME/.claude/CLAUDE.md"
fi
rm -f "$HOME/.devin/global_rules.md"

validate

printf '%-55s %s\n' "DESTINO" "ARQUIVOS"
for d in "$HOME/.config/devin" "$HOME/.devin/rules" "$HOME/.config/devin/skills" \
         "$HOME/.codeium/windsurf/memories" "$HOME/.cursor/rules"; do
  c=$(find "$d" -type f 2>/dev/null | wc -l | tr -d ' ')
  printf '%-55s %s\n' "$d" "$c"
done

[[ $FAILED -eq 0 ]] || exit 1
