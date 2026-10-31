#!/usr/bin/env bash
# Diagnoses and repairs safe local AI Kit state. Usage: doctor.sh
set -euo pipefail

KIT="${AI_KIT_DIR:-$HOME/.ai-kit}"
source "$(dirname "${BASH_SOURCE[0]}")/codex-bin.sh"
HEADER="# Global Rules — AI Kit"
FAILURES=0
ORIGIN_SHA=""
AUTO_COMPACT_WINDOW="200k"

ok() {
  printf 'ok: %s\n' "$*"
}

fix() {
  printf 'fix: %s\n' "$*"
}

warn() {
  printf 'warn: %s\n' "$*"
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

json_contains() {
  local payload="$1"
  local needle="$2"
  python3 - "$needle" "$payload" <<'PY'
import json
import sys

try:
    data = json.loads(sys.argv[2])
except json.JSONDecodeError:
    raise SystemExit(1)
needle = sys.argv[1]
def contains(value):
    if isinstance(value, str):
        return value == needle
    if isinstance(value, list):
        return any(contains(item) for item in value)
    if isinstance(value, dict):
        return any(contains(item) for item in value.values())
    return False
raise SystemExit(0 if contains(data) else 1)
PY
}

# KIT-013: Claude caches a plugin per version, so a kit change without a version bump leaves the cache stale.
# Prints each user-scope <plugin>@ai-kit whose cache differs from its directory in the marketplace clone.
claude_stale_plugins() {
  python3 - "$1" "$2" <<'PY'
import hashlib
import json
import os
import sys
from pathlib import Path

RUNTIME_MARKERS = {".in_use"}

def tree_hash(root):
    digest = hashlib.sha256()
    for directory, dirs, files in os.walk(root):
        if Path(directory) == root:
            # Claude keeps its .in_use process markers at the top of a cache directory.
            dirs[:] = [name for name in dirs if name not in RUNTIME_MARKERS]
            files = [name for name in files if name not in RUNTIME_MARKERS]
        dirs.sort()
        for name in sorted(files):
            path = Path(directory, name)
            relative = path.relative_to(root)
            digest.update(str(relative).encode() + b"\0")
            digest.update(b"link:" + os.readlink(path).encode() if path.is_symlink() else path.read_bytes())
            digest.update(b"\0")
    return digest.hexdigest()

try:
    marketplaces = json.loads(sys.argv[1])
    plugins = json.loads(sys.argv[2])
except json.JSONDecodeError:
    raise SystemExit(0)
if not isinstance(marketplaces, list) or not isinstance(plugins, list):
    raise SystemExit(0)
location = next((m.get("installLocation") for m in marketplaces if m.get("name") == "ai-kit"), None)
if not location:
    raise SystemExit(0)
try:
    catalog = json.loads(Path(location, ".claude-plugin/marketplace.json").read_text(encoding="utf-8"))
except (OSError, json.JSONDecodeError):
    raise SystemExit(0)
sources = {entry.get("name"): entry.get("source") for entry in catalog.get("plugins", [])}
stale = set()
for plugin in plugins:
    name, _, marketplace = str(plugin.get("id", "")).partition("@")
    source = sources.get(name)
    install = plugin.get("installPath")
    if marketplace != "ai-kit" or plugin.get("scope", "user") != "user" or not isinstance(source, str) or not install:
        continue
    source_dir = Path(location, source)
    if source_dir.is_dir() and (not Path(install).is_dir() or tree_hash(source_dir) != tree_hash(Path(install))):
        stale.add(name)
for name in sorted(stale):
    print(name)
PY
}

ensure_agents_link() {
  local destination="$HOME/.codex/AGENTS.md"
  local expected="$KIT/plugins/core/AGENTS.md"
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
      fix "codex AGENTS.md symlink repointed from $current to $expected"
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

ensure_claude_links() {
  local claude_md="$HOME/.claude/CLAUDE.md"
  local expected_agents="$KIT/plugins/core/AGENTS.md"
  local current
  local backup
  local name
  local destination
  local expected
  mkdir -p "$HOME/.claude/rules"
  if [[ -L "$claude_md" ]]; then
    current="$(readlink "$claude_md")"
    if [[ "$current" == "$expected_agents" ]]; then
      ok "claude CLAUDE.md symlink"
    elif [[ "$current" == "$KIT/"* ]]; then
      rm "$claude_md"
      ln -s "$expected_agents" "$claude_md"
      fix "claude CLAUDE.md symlink repointed from $current to $expected_agents"
    else
      fail "$claude_md points to $current, not kit-managed; move it by hand"
    fi
  elif [[ -f "$claude_md" ]]; then
    backup="$claude_md.bak.$(date +%Y%m%d-%H%M%S)"
    mv "$claude_md" "$backup"
    ln -s "$expected_agents" "$claude_md"
    fix "claude CLAUDE.md backed up to $backup and symlinked"
  elif [[ -e "$claude_md" ]]; then
    fail "$claude_md is not a file or symlink; remove it by hand"
  else
    ln -s "$expected_agents" "$claude_md"
    fix "claude CLAUDE.md symlink created"
  fi

  local rule_file
  local plugin
  # Default 0 since P2-15: consumer repos carry .claude/rules; set 1 to keep user-level symlinks.
  if [[ "${AI_KIT_USER_RULES:-0}" == "0" ]]; then
    for destination in "$HOME/.claude/rules/"*.md; do
      [[ -L "$destination" ]] || continue
      current="$(readlink "$destination")"
      case "$current" in
        "$KIT"/plugins/*/rules/*)
          rm "$destination"
          fix "removed user-level claude rule symlink ${destination##*/} (AI_KIT_USER_RULES=0)"
          ;;
      esac
    done
    ok "user-level claude rules disabled (AI_KIT_USER_RULES=0); repos carry .claude/rules via sync-project.sh"
    return
  fi
  for rule_file in "$KIT"/plugins/*/rules/*.md; do
    [[ -f "$rule_file" ]] || continue
    plugin="$(basename "$(dirname "$(dirname "$rule_file")")")"
    name="${rule_file##*/}"
    name="${name%.md}"
    destination="$HOME/.claude/rules/$plugin-$name.md"
    if [[ -L "$destination" ]]; then
      current="$(readlink "$destination")"
      if [[ "$current" == "$rule_file" ]]; then
        ok "claude rule symlink $plugin-$name"
      elif [[ "$current" == "$KIT/"* ]]; then
        rm "$destination"
        ln -s "$rule_file" "$destination"
        fix "claude rule symlink repaired for $plugin-$name"
      else
        fail "$destination points to $current, not kit-managed; move it by hand"
      fi
    elif [[ -e "$destination" ]]; then
      fail "$destination is not a managed symlink; move it by hand"
    else
      ln -s "$rule_file" "$destination"
      fix "claude rule symlink created for $plugin-$name"
    fi
  done

  for destination in "$HOME/.claude/rules/"*.md; do
    [[ -L "$destination" ]] || continue
    current="$(readlink "$destination")"
    case "$current" in
      "$KIT"/plugins/*/rules/*)
        if [[ ! -e "$current" ]]; then
          rm "$destination"
          fix "removed stale claude rule symlink $(basename "$destination")"
        fi
        ;;
    esac
  done
}

# KIT-010: Claude Code compacts a conversation at its context window; the kit caps it at 200k so a long session
# stops re-reading up to 1M tokens on every turn. An explicit owner value is kept and reported.
ensure_claude_auto_compact() {
  local settings="$HOME/.claude/settings.json"
  local result
  if [[ -n "${CLAUDE_CODE_AUTO_COMPACT_WINDOW:-}" ]]; then
    warn "CLAUDE_CODE_AUTO_COMPACT_WINDOW=$CLAUDE_CODE_AUTO_COMPACT_WINDOW overrides autoCompactWindow in $settings"
  fi
  if ! result="$(python3 - "$settings" "$AUTO_COMPACT_WINDOW" <<'PY'
import json
import os
import re
import sys

path, kit_value = sys.argv[1], sys.argv[2]

def tokens(value):
    match = re.fullmatch(r"(\d+(?:\.\d+)?)([kKmM]?)", str(value).strip())
    if not match:
        return None
    scale = {"": 1, "k": 1_000, "m": 1_000_000}[match.group(2).lower()]
    return float(match.group(1)) * scale

try:
    with open(path, encoding="utf-8") as handle:
        settings = json.load(handle)
except FileNotFoundError:
    settings = {}
except (OSError, json.JSONDecodeError) as error:
    print(f"fail {path} unreadable ({error}); autoCompactWindow not checked")
    raise SystemExit(0)
if not isinstance(settings, dict):
    print(f"fail {path} is not a JSON object; autoCompactWindow not checked")
    raise SystemExit(0)
current = settings.get("autoCompactWindow")
if current is None:
    settings["autoCompactWindow"] = kit_value
    os.makedirs(os.path.dirname(path), exist_ok=True)
    temp = path + ".ai-kit-tmp"
    with open(temp, "w", encoding="utf-8") as handle:
        json.dump(settings, handle, indent=2, ensure_ascii=False)
        handle.write("\n")
    os.replace(temp, path)
    print(f"fix claude autoCompactWindow set to {kit_value} in {path} (KIT-010)")
elif tokens(current) is not None and tokens(current) <= tokens(kit_value):
    print(f"ok claude autoCompactWindow {current}")
else:
    print(f"warn claude autoCompactWindow '{current}' is above the kit's {kit_value} — kept (owner's choice)")
PY
)"; then
    fail "cannot check autoCompactWindow in $settings"
    return
  fi
  case "$result" in
    "fix "*) fix "${result#fix }" ;;
    "ok "*) ok "${result#ok }" ;;
    "warn "*) warn "${result#warn }" ;;
    *) fail "${result#fail }" ;;
  esac
}

devin_plugin_record() {
  python3 - "$1" <<'PY'
import json
import sys

try:
    data = json.load(open(sys.argv[1], encoding="utf-8"))
except (OSError, json.JSONDecodeError):
    raise SystemExit(2)
entry = next((item for item in data.get("resolved", []) if item.get("name") == "core"), None)
if entry is None:
    entry = next((item for item in data.get("resolved", []) if item.get("name") == "agent-rules-kit"), None)
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
  for skill_file in "$KIT"/plugins/*/skills/*/SKILL.md; do
    [[ -f "$skill_file" ]] || continue
    expected_count=$((expected_count + 1))
    name="$(basename "$(dirname "$skill_file")")"
    destination="$codex_skills/$name"
    expected="$(dirname "$skill_file")"
    if [[ -L "$destination" ]]; then
      current="$(readlink "$destination")"
      if [[ "$current" == "$expected" ]]; then
        active_count=$((active_count + 1))
      elif [[ "$current" == "$KIT"/plugins/*/skills/* ]]; then
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
      "$KIT"/plugins/*/skills/*)
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
      "$KIT"/plugins/*/skills/*)
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
    if grep -q '"name": "ai-kit"' "$lock"; then
      fail "legacy 'ai-kit' plugin installed — run: devin plugins remove ai-kit && devin plugins install ChristianPrzybulinski/agent-rules-kit"
    else
      fail "core plugin not installed — run: devin plugins install ChristianPrzybulinski/agent-rules-kit"
    fi
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
      if devin plugins update >/dev/null 2>&1 \
          && updated_record="$(devin_plugin_record "$lock" 2>/dev/null)" \
          && [[ "${updated_record#*|}" == "$ORIGIN_SHA" ]]; then
        fix "devin plugins updated to origin/main"
      else
        fail "devin plugin sha differs from origin/main and update failed"
      fi
    else
      fail "devin plugin sha differs from origin/main; install devin and run: devin plugins update"
    fi
  fi
else
  ok "devin plugin lock absent — skipped"
fi

devin_config="$HOME/.config/devin/config.json"
mkdir -p "$(dirname "$devin_config")"
if ! config_result="$(python3 - "$devin_config" <<'PY'
import json
import sys
from pathlib import Path

path = Path(sys.argv[1])
expected = {
    "agents_standard": True,
    "cursor": False,
    "windsurf": False,
    "claude": False,
    "copilot": False,
    "opencode": False,
    "zed": False,
}
try:
    data = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {"version": 1}
except (OSError, json.JSONDecodeError) as error:
    print(error, file=sys.stderr)
    raise SystemExit(2)
if not isinstance(data, dict):
    print("top-level Devin config must be an object", file=sys.stderr)
    raise SystemExit(2)
before = data.get("read_config_from")
status = "unchanged"
if before != expected:
    data["read_config_from"] = expected
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    status = "changed"
print("\t".join((status, json.dumps(before, separators=(",", ":")),
                 json.dumps(expected, separators=(",", ":")))))
PY
)"; then
  fail "cannot merge read_config_from into $devin_config"
else
  config_status="${config_result%%$'\t'*}"
  config_values="${config_result#*$'\t'}"
  before_config="${config_values%%$'\t'*}"
  after_config="${config_values#*$'\t'}"
  if [[ "$config_status" == "changed" ]]; then
    fix "devin read_config_from $before_config → $after_config"
  else
    ok "devin read_config_from limited to agents_standard"
  fi
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
  plugin_names=()
  plugin_pattern=""
  for plugin_dir in "$KIT"/plugins/*/; do
    [[ -d "$plugin_dir/.devin-plugin" || -d "$plugin_dir/.claude-plugin" || -f "$plugin_dir/plugin.json" ]] || continue
    plugin_name="$(basename "$plugin_dir")"
    plugin_names+=("$plugin_name")
    plugin_pattern="${plugin_pattern}${plugin_pattern:+|}${plugin_name}"
  done
  missing_plugins=()
  for plugin_name in "${plugin_names[@]:-}"; do
    [[ -n "$plugin_name" ]] || continue
    if [[ "$plugins" == *"$plugin_name@ai-kit"* ]]; then
      continue
    fi
    if [[ "$marketplace_ready" -eq 1 ]] && "$codex" plugin add "$plugin_name@ai-kit" >/dev/null 2>&1; then
      fix "codex plugin $plugin_name@ai-kit installed"
    else
      missing_plugins+=("$plugin_name")
      plugin_ready=0
    fi
  done
  if [[ "${#missing_plugins[@]}" -eq 0 ]]; then
    ok "codex plugins installed (${#plugin_names[@]} entries)"
  else
    fail "codex plugins missing and add failed: ${missing_plugins[*]} — run: codex plugin add <name>@ai-kit"
  fi

  if [[ "$plugin_ready" -eq 1 ]]; then
    exposed="$("$codex" debug prompt-input "list skills" 2>/dev/null | grep -oE "(${plugin_pattern}):" | wc -l | tr -d ' ' || true)"
    if [[ "$exposed" -eq 0 ]]; then
      ensure_codex_fallback
    else
      remove_codex_fallback
      ok "codex plugin exposes $exposed kit skills"
    fi
  fi
elif [[ -f "$HOME/.codex/config.toml" || -f "$HOME/.codex/auth.json" ]]; then
  ok "codex CLI not found; desktop app detected — fallback symlinks maintained (openai/codex#22078)"
  ensure_codex_fallback
else
  ok "codex not installed — skipped"
fi

# 6. Claude plugin and shared instructions
if command -v claude >/dev/null 2>&1; then
  claude_marketplace_ready=1
  claude_marketplaces="$(claude plugin marketplace list --json 2>/dev/null || true)"
  if json_contains "$claude_marketplaces" "ai-kit"; then
    ok "claude marketplace ai-kit registered"
  elif claude plugin marketplace add ChristianPrzybulinski/agent-rules-kit --json >/dev/null 2>&1; then
    fix "claude marketplace ai-kit registered"
  else
    fail "claude marketplace ai-kit missing and add failed — run: claude plugin marketplace add ChristianPrzybulinski/agent-rules-kit"
    claude_marketplace_ready=0
  fi

  claude_plugins="$(claude plugin list --json 2>/dev/null || true)"
  if json_contains "$claude_plugins" "all@ai-kit"; then
    ok "claude bundle all@ai-kit installed"
  elif [[ "$claude_marketplace_ready" -eq 1 ]] \
      && claude plugin install all@ai-kit --json >/dev/null 2>&1; then
    fix "claude bundle all@ai-kit installed"
  else
    fail "claude bundle all@ai-kit missing and install failed — run: claude plugin install all@ai-kit"
  fi
  if stale_plugins="$(claude_stale_plugins "$claude_marketplaces" "$claude_plugins")"; then
    for plugin_name in $stale_plugins; do
      warn "claude plugin $plugin_name@ai-kit cache differs from the kit — run platforms/tools/refresh.sh"
    done
  else
    warn "cannot compare Claude plugin caches with the kit"
  fi
  ensure_claude_links
  ensure_claude_auto_compact

  if [[ -L "$HOME/.claude/CLAUDE.md" ]]; then
    claude_import="$(python3 - "$devin_config" <<'PY'
import json
import sys
try:
    with open(sys.argv[1], encoding="utf-8") as handle:
        value = (json.load(handle).get("read_config_from") or {}).get("claude")
except (OSError, json.JSONDecodeError, AttributeError):
    value = None
print(json.dumps(value))
PY
)"
    if [[ "$claude_import" != "false" ]]; then
      fail "$HOME/.claude/CLAUDE.md is linked while Devin read_config_from.claude is not false"
    fi
  fi
else
  warn "claude not installed — skipped"
fi

# 7. Kit gates
validator="$KIT/platforms/ci/validations/check_kit.py"
agents_limit="$(awk -F= '/^AGENTS_MAX_LINES = / {gsub(/[[:space:]]/, "", $2); print $2; exit}' "$validator")"
description_budget="$(awk -F= '/^DESCRIPTIONS_BUDGET = / {gsub(/[[:space:]]/, "", $2); print $2; exit}' "$validator")"
if [[ ! "$agents_limit" =~ ^[0-9]+$ || ! "$description_budget" =~ ^[0-9]+$ ]]; then
  fail "cannot read validator limits"
else
  agents_lines="$(wc -l < "$KIT/plugins/core/AGENTS.md" | tr -d ' ')"
  if [[ "$agents_lines" -le "$agents_limit" ]]; then
    ok "AGENTS.md $agents_lines lines (limit $agents_limit)"
  else
    fail "AGENTS.md $agents_lines lines exceeds $agents_limit"
  fi

  if description_total="$(python3 - "$KIT" <<'PY'
from pathlib import Path
import sys

total = 0
for skill in Path(sys.argv[1], "plugins").glob("*/skills/*/SKILL.md"):
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
