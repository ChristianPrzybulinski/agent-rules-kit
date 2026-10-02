#!/usr/bin/env bash
# Diagnoses and repairs safe local AI Kit state. Usage: doctor.sh
set -euo pipefail

KIT="${AI_KIT_DIR:-$HOME/.ai-kit}"
HEADER="# Global Rules — AI Kit"
FAILURES=0
ORIGIN_SHA=""

ok() {
  printf 'ok: %s\n' "$*"
}

fix() {
  printf 'fix: %s\n' "$*"
}

fail() {
  printf 'FAIL: %s\n' "$*" >&2
  FAILURES=$((FAILURES + 1))
}

finish() {
  if [[ "$FAILURES" -eq 0 ]]; then
    printf 'doctor: OK\n'
    exit 0
  fi
  printf 'doctor: %s failure(s)\n' "$FAILURES"
  exit 1
}

codex_bin() {
  local candidate
  [[ "${AI_KIT_NO_CODEX_CLI:-0}" != "1" ]] || return 1
  candidate="$(command -v codex 2>/dev/null || true)"
  if [[ -n "$candidate" && -x "$candidate" ]]; then
    printf '%s\n' "$candidate"
    return 0
  fi
  for candidate in \
    /Applications/ChatGPT.app/Contents/Resources/codex-cli/bin/codex \
    /Applications/Codex.app/Contents/Resources/codex-cli/bin/codex; do
    if [[ -x "$candidate" ]]; then
      printf '%s\n' "$candidate"
      return 0
    fi
  done
  candidate="$(find "$HOME/.cache/codex-runtimes" /Applications/ChatGPT.app /Applications/Codex.app \
    -type f -name codex -perm -u+x 2>/dev/null | head -1 || true)"
  if [[ -n "$candidate" && -x "$candidate" ]]; then
    printf '%s\n' "$candidate"
    return 0
  fi
  return 1
}

ensure_agents_link() {
  local destination="$HOME/.codex/AGENTS.md"
  local expected="$KIT/AGENTS.md"
  local current
  local backup
  mkdir -p "$HOME/.codex"
  if [[ -L "$destination" ]]; then
    current="$(readlink "$destination")"
    if [[ "$current" == "$expected" ]]; then
      ok "codex AGENTS.md symlink"
    elif [[ "$current" == "$KIT/"* ]]; then
      rm "$destination"
      ln -s "$expected" "$destination"
      fix "codex AGENTS.md symlink repaired"
    else
      fail "$destination points to $current, not kit-managed; move it by hand"
    fi
    return
  fi
  if [[ -f "$destination" ]]; then
    if grep -Fxq "$HEADER" "$destination"; then
      backup="$destination.bak.$(date +%Y%m%d-%H%M%S)"
      mv "$destination" "$backup"
      ln -s "$expected" "$destination"
      fix "kit AGENTS.md backed up to $backup and symlinked"
    else
      fail "$destination is not kit-managed; move it before creating the symlink"
    fi
    return
  fi
  if [[ -e "$destination" ]]; then
    fail "$destination is not a file or symlink; remove it by hand"
    return
  fi
  ln -s "$expected" "$destination"
  fix "codex AGENTS.md symlink created"
}

devin_plugin_record() {
  python3 - "$1" <<'PY'
import json
import sys

try:
    data = json.load(open(sys.argv[1], encoding="utf-8"))
except (OSError, json.JSONDecodeError):
    raise SystemExit(2)
entry = next((item for item in data.get("resolved", []) if item.get("name") == "ai-kit"), None)
if entry is None:
    print("MISSING")
else:
    spec = entry.get("spec") or {}
    resolved = entry.get("resolved") or {}
    print(f"{spec.get('ref') or '<absent>'}|{resolved.get('sha') or '<missing>'}")
PY
}

remove_legacy_file() {
  local path="$1"
  if [[ ! -e "$path" && ! -L "$path" ]]; then
    return
  fi
  if [[ -f "$path" ]] && grep -Fxq "$HEADER" "$path"; then
    rm "$path"
    fix "removed legacy $path"
  else
    fail "$path is not kit-managed; remove by hand if unwanted"
  fi
}

remove_marked_skills() {
  local base="$1"
  local marker
  local directory
  [[ -d "$base" ]] || return 0
  for marker in "$base"/*/.agent-rules-kit; do
    [[ -f "$marker" ]] || continue
    directory="${marker%/.agent-rules-kit}"
    rm -rf "$directory"
    fix "removed legacy skill $directory"
  done
}

ensure_codex_fallback() {
  local codex_skills="$HOME/.codex/skills"
  local expected_count=0
  local active_count=0
  local skill_file
  local name
  local destination
  local expected
  local current
  local target
  mkdir -p "$codex_skills"
  for skill_file in "$KIT"/skills/*/SKILL.md; do
    [[ -f "$skill_file" ]] || continue
    expected_count=$((expected_count + 1))
    name="$(basename "$(dirname "$skill_file")")"
    destination="$codex_skills/$name"
    expected="$KIT/skills/$name"
    if [[ -L "$destination" ]]; then
      current="$(readlink "$destination")"
      if [[ "$current" == "$expected" ]]; then
        active_count=$((active_count + 1))
      elif [[ "$current" == "$KIT/skills/"* ]]; then
        rm "$destination"
        ln -s "$expected" "$destination"
        fix "codex fallback repaired for $name"
        active_count=$((active_count + 1))
      else
        fail "$destination points to $current, not kit-managed; move it by hand"
      fi
    elif [[ -e "$destination" ]]; then
      fail "$destination is not a managed symlink; move it by hand"
    else
      ln -s "$expected" "$destination"
      fix "codex fallback created for $name"
      active_count=$((active_count + 1))
    fi
  done
  for destination in "$codex_skills"/*; do
    [[ -L "$destination" ]] || continue
    target="$(readlink "$destination")"
    case "$target" in
      "$KIT"/skills/*)
        if [[ ! -e "$target" ]]; then
          rm "$destination"
          fix "removed stale codex fallback $(basename "$destination")"
        fi
        ;;
    esac
  done
  if [[ "$active_count" -eq "$expected_count" ]]; then
    ok "codex fallback active ($active_count symlinks) — openai/codex#22078"
  fi
}

remove_codex_fallback() {
  local codex_skills="$HOME/.codex/skills"
  local removed=0
  local destination
  local target
  [[ -d "$codex_skills" ]] || return 0
  for destination in "$codex_skills"/*; do
    [[ -L "$destination" ]] || continue
    target="$(readlink "$destination")"
    case "$target" in
      "$KIT"/skills/*)
        rm "$destination"
        removed=$((removed + 1))
        ;;
    esac
  done
  if [[ "$removed" -gt 0 ]]; then
    fix "codex plugin exposes skills; fallback symlinks removed"
  fi
}

# 1. Clone state
if [[ ! -d "$KIT/.git" ]]; then
  fail "$KIT is not a git clone — run platforms/tools/bootstrap.sh"
  finish
fi
ok "kit clone exists"

branch="$(git -C "$KIT" branch --show-current 2>/dev/null || true)"
if [[ "$branch" == "main" ]]; then
  ok "kit branch is main"
else
  fail "kit branch is '$branch' — run platforms/tools/refresh.sh"
fi

status="$(git -C "$KIT" status --short 2>/dev/null || true)"
if [[ -z "$status" ]]; then
  ok "kit working tree clean"
else
  fail "kit working tree is dirty"
  printf '%s\n' "$status" >&2
fi

if ORIGIN_SHA="$(git -C "$KIT" rev-parse origin/main 2>/dev/null)"; then
  head_sha="$(git -C "$KIT" rev-parse HEAD 2>/dev/null || true)"
  if [[ "$head_sha" == "$ORIGIN_SHA" ]]; then
    ok "kit HEAD matches origin/main (${ORIGIN_SHA:0:7})"
  else
    fail "kit HEAD differs from origin/main — run platforms/tools/refresh.sh"
  fi
else
  ORIGIN_SHA=""
  fail "origin/main is unavailable — run platforms/tools/refresh.sh"
fi

# 2. Codex always-on
ensure_agents_link

# 3. Devin plugin
lock="$HOME/.local/share/devin/cli/plugins/lock.json"
if [[ -f "$lock" ]]; then
  if ! record="$(devin_plugin_record "$lock" 2>/dev/null)"; then
    fail "$lock is not readable JSON"
  elif [[ "$record" == "MISSING" ]]; then
    fail "ai-kit plugin not installed — run: devin plugins install ChristianPrzybulinski/agent-rules-kit"
  else
    ref="${record%%|*}"
    resolved_sha="${record#*|}"
    if [[ "$ref" == "main" || "$ref" == "<absent>" ]]; then
      ok "devin plugin ref is main"
    else
      fail "plugin ref is '$ref' — switch to main in Customize → Plugins → Plugin settings → Edit manifest"
    fi
    if [[ -z "$ORIGIN_SHA" ]]; then
      fail "cannot compare devin plugin sha without origin/main"
    elif [[ "$resolved_sha" == "$ORIGIN_SHA" ]]; then
      ok "devin plugin sha matches origin/main"
    elif command -v devin >/dev/null 2>&1; then
      if devin plugins update ai-kit >/dev/null 2>&1 \
          && updated_record="$(devin_plugin_record "$lock" 2>/dev/null)" \
          && [[ "${updated_record#*|}" == "$ORIGIN_SHA" ]]; then
        fix "devin plugin updated to origin/main"
      else
        fail "devin plugin sha differs from origin/main and update failed"
      fi
    else
      fail "devin plugin sha differs from origin/main; install devin and run: devin plugins update ai-kit"
    fi
  fi
else
  ok "devin plugin lock absent — skipped"
fi

# 4. Legacy destinations
remove_legacy_file "$HOME/.config/devin/AGENTS.md"
remove_legacy_file "$HOME/.codeium/windsurf/memories/global_rules.md"
remove_marked_skills "$HOME/.agents/skills"
remove_marked_skills "$HOME/.codeium/windsurf/skills"
remove_marked_skills "$HOME/.codex/skills"

if [[ -d "$HOME/.config/agent-rules-kit" ]]; then
  rm -rf "$HOME/.config/agent-rules-kit"
  fix "removed legacy $HOME/.config/agent-rules-kit"
fi

legacy_rules="$HOME/.devin/rules"
if [[ -d "$legacy_rules" ]]; then
  all_kit=1
  while IFS= read -r -d '' rule_file; do
    if ! grep -Fxq "$HEADER" "$rule_file"; then
      all_kit=0
    fi
  done < <(find "$legacy_rules" -type f -print0)
  if [[ "$all_kit" -eq 1 ]]; then
    rm -rf "$legacy_rules"
    fix "removed legacy $legacy_rules"
  else
    fail "$legacy_rules contains non-kit files; remove by hand if unwanted"
  fi
fi
ok "legacy destinations checked"

# 5. Codex plugin and fallback
codex="$(codex_bin || true)"
if [[ -n "$codex" ]]; then
  marketplace_ready=1
  marketplaces="$("$codex" plugin marketplace list 2>/dev/null || true)"
  if [[ "$marketplaces" == *"ai-kit"* ]]; then
    ok "codex marketplace ai-kit registered"
  elif "$codex" plugin marketplace add ChristianPrzybulinski/agent-rules-kit --ref main >/dev/null 2>&1; then
    fix "codex marketplace ai-kit registered"
  else
    fail "codex marketplace ai-kit missing and add failed — run: codex plugin marketplace add ChristianPrzybulinski/agent-rules-kit --ref main"
    marketplace_ready=0
  fi

  plugin_ready=1
  plugins="$("$codex" plugin list 2>/dev/null || true)"
  if [[ "$plugins" == *"ai-kit@ai-kit"* ]]; then
    ok "codex plugin ai-kit@ai-kit installed"
  elif [[ "$marketplace_ready" -eq 1 ]] && "$codex" plugin add ai-kit@ai-kit >/dev/null 2>&1; then
    fix "codex plugin ai-kit@ai-kit installed"
  else
    fail "codex plugin ai-kit@ai-kit missing and add failed — run: codex plugin add ai-kit@ai-kit"
    plugin_ready=0
  fi

  if [[ "$plugin_ready" -eq 1 ]]; then
    exposed="$("$codex" debug prompt-input "list skills" 2>/dev/null | grep -o 'ai-kit:' | wc -l | tr -d ' ' || true)"
    if [[ "$exposed" -eq 0 ]]; then
      ensure_codex_fallback
    else
      remove_codex_fallback
      ok "codex plugin exposes $exposed ai-kit skills"
    fi
  fi
elif [[ -f "$HOME/.codex/config.toml" || -f "$HOME/.codex/auth.json" ]]; then
  ok "codex CLI not found; desktop app detected — fallback symlinks maintained (openai/codex#22078)"
  ensure_codex_fallback
else
  ok "codex not installed — skipped"
fi

# 6. Kit gates
validator="$KIT/platforms/ci/validations/check_kit.py"
agents_limit="$(awk -F= '/^AGENTS_MAX_LINES = / {gsub(/[[:space:]]/, "", $2); print $2; exit}' "$validator")"
description_budget="$(awk -F= '/^DESCRIPTIONS_BUDGET = / {gsub(/[[:space:]]/, "", $2); print $2; exit}' "$validator")"
if [[ ! "$agents_limit" =~ ^[0-9]+$ || ! "$description_budget" =~ ^[0-9]+$ ]]; then
  fail "cannot read validator limits"
else
  agents_lines="$(wc -l < "$KIT/AGENTS.md" | tr -d ' ')"
  if [[ "$agents_lines" -le "$agents_limit" ]]; then
    ok "AGENTS.md $agents_lines lines (limit $agents_limit)"
  else
    fail "AGENTS.md $agents_lines lines exceeds $agents_limit"
  fi

  if description_total="$(python3 - "$KIT" <<'PY'
from pathlib import Path
import sys

total = 0
for skill in Path(sys.argv[1], "skills").glob("*/SKILL.md"):
    for line in skill.read_text(encoding="utf-8").splitlines():
        if line.startswith("description: "):
            value = line.removeprefix("description: ")
            if len(value) >= 2 and value[0] == value[-1] and value[0] in "'\"":
                value = value[1:-1]
            total += len(value)
            break
print(total)
PY
)"; then
    if [[ "$description_total" -le "$description_budget" ]]; then
      ok "skill descriptions $description_total chars (budget $description_budget)"
    else
      fail "skill descriptions $description_total chars exceeds $description_budget"
    fi
  else
    fail "cannot count skill descriptions"
  fi
fi

finish
