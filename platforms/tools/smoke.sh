#!/usr/bin/env bash
# Exercises bootstrap and doctor in isolated homes. Usage: smoke.sh [--main]
#   --main  stops after the main path: bootstrap into an empty home, the Codex AGENTS.md link and its repoints, and
#           a clean doctor run (KIT-077: the integration test test_smoke.py runs it on a pull request; the whole
#           script is the functional layer's, on main, nightly and before a release)
set -euo pipefail

MODE="${1:-}"
case "$MODE" in
  ''|--main) ;;
  *) printf 'usage: smoke.sh [--main]\n' >&2; exit 2 ;;
esac

KIT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
ROOT="$(mktemp -d)"
SOURCE="$ROOT/source"
TEST_HOME="$ROOT/home"
RESTRICTED_PATH="/usr/bin:/bin"
export AI_KIT_NO_CODEX_CLI=1
# KIT-056: refresh runs session_audit.py, which honors these; keep it on the throwaway homes, never the real state.
# KIT-081: refresh.sh and doctor.sh read Claude Code's plugin folder from the last two; keep it in the homes too.
unset XDG_STATE_HOME CODEX_HOME CODEX_SQLITE_HOME CLAUDE_CONFIG_DIR CLAUDE_CODE_PLUGIN_CACHE_DIR

cleanup() {
  rm -rf "$ROOT"
}
trap cleanup EXIT

fail() {
  printf 'FAIL: smoke: %s\n' "$*" >&2
  exit 1
}

# KIT-010: the stub's autoCompactWindow as JSON text, so the number 300000 and the string "300000" differ.
stub_compact_window() {
  python3 -c 'import json,sys; print(json.dumps(json.load(open(sys.argv[1]))["autoCompactWindow"]))' \
    "$STUB_HOME/.claude/settings.json"
}

set_stub_compact_window() {
  python3 - "$STUB_HOME/.claude/settings.json" "$1" <<'PY'
import json
import sys
settings = json.load(open(sys.argv[1]))
settings["autoCompactWindow"] = json.loads(sys.argv[2])
json.dump(settings, open(sys.argv[1], "w"), indent=2)
PY
}

mkdir -p "$SOURCE" "$TEST_HOME"
(
  cd "$KIT_DIR"
  tar --exclude='.git' -cf - .
) | tar -xf - -C "$SOURCE"

# Lifecycle behavior is independent of Wave 2 description shortening. Normalize
# only the throwaway fixture so doctor can exercise its passing budget path.
python3 - "$SOURCE" <<'PY'
from pathlib import Path
import sys

replacement = "description: Smoke lifecycle fixture. Use when testing bootstrap and doctor. Not for production guidance (skill review)."
for skill in Path(sys.argv[1], "plugins").glob("*/skills/*/SKILL.md"):
    lines = skill.read_text(encoding="utf-8").splitlines()
    for index, line in enumerate(lines):
        if line.startswith("description: "):
            lines[index] = replacement
            break
    skill.write_text("\n".join(lines) + "\n", encoding="utf-8")
PY

git -C "$SOURCE" init -q -b main
git -C "$SOURCE" add -A
# Git >= 2.4x starts `git maintenance run --auto --detach` after a commit; it packs the fixture's loose objects
# while bootstrap.sh clones the fixture, and the clone fails mid-copy (KIT-003)
git -C "$SOURCE" -c maintenance.auto=false -c gc.auto=0 -c user.name=smoke -c user.email=smoke@example.invalid commit -q -m "test fixture"
# #271: the user install follows the newest vX.Y.Z on origin/main, so the fixture is a release
git -C "$SOURCE" tag v0.0.0

bootstrap_output="$ROOT/bootstrap.out"
if ! env HOME="$TEST_HOME" PATH="$RESTRICTED_PATH" \
    AI_KIT_DIR="$TEST_HOME/.ai-kit" AI_KIT_SOURCE="$SOURCE" AI_KIT_NO_LAUNCHD=1 \
    "$KIT_DIR/platforms/tools/bootstrap.sh" >"$bootstrap_output" 2>&1; then
  cat "$bootstrap_output" >&2
  fail "bootstrap failed"
fi

grep -Fq 'fix: kit clone at release v0.0.0' "$bootstrap_output" || fail "bootstrap did not check out the release"
git -C "$TEST_HOME/.ai-kit" symbolic-ref -q HEAD >/dev/null && fail "bootstrap left the clone on a branch, not the release"

agents_link="$TEST_HOME/.codex/AGENTS.md"
[[ -L "$agents_link" ]] || fail "Codex AGENTS.md is not a symlink"
resolved="$(python3 -c 'import os,sys; print(os.path.realpath(sys.argv[1]))' "$agents_link")"
expected_resolved="$(python3 -c 'import os,sys; print(os.path.realpath(sys.argv[1]))' "$TEST_HOME/.ai-kit/plugins/guardrails/AGENTS.md")"
[[ "$resolved" == "$expected_resolved" ]] || fail "Codex AGENTS.md resolves to $resolved"

rm "$agents_link"
ln -s "$TEST_HOME/.ai-kit/AGENTS.md" "$agents_link"
if ! env HOME="$TEST_HOME" PATH="$RESTRICTED_PATH" AI_KIT_DIR="$TEST_HOME/.ai-kit" \
    "$TEST_HOME/.ai-kit/platforms/tools/doctor.sh" >"$ROOT/doctor-repoint.out" 2>&1; then
  cat "$ROOT/doctor-repoint.out" >&2
  fail "doctor failed to repoint the legacy AGENTS.md symlink"
fi
grep -Fq 'fix: codex AGENTS.md symlink repointed' "$ROOT/doctor-repoint.out" \
  || fail "legacy AGENTS.md symlink repoint was not reported"
[[ "$(readlink "$agents_link")" == "$TEST_HOME/.ai-kit/plugins/guardrails/AGENTS.md" ]] \
  || fail "legacy AGENTS.md symlink was not repointed"

rm "$agents_link"
ln -s "$TEST_HOME/.ai-kit/kit/AGENTS.md" "$agents_link"
if ! env HOME="$TEST_HOME" PATH="$RESTRICTED_PATH" AI_KIT_DIR="$TEST_HOME/.ai-kit" \
    "$TEST_HOME/.ai-kit/platforms/tools/doctor.sh" >"$ROOT/doctor-repoint-kit.out" 2>&1; then
  cat "$ROOT/doctor-repoint-kit.out" >&2
  fail "doctor failed to repoint the former kit/ AGENTS.md symlink"
fi
[[ "$(readlink "$agents_link")" == "$TEST_HOME/.ai-kit/plugins/guardrails/AGENTS.md" ]] \
  || fail "former kit/ AGENTS.md symlink was not repointed"

rm "$agents_link"
ln -s "$TEST_HOME/.ai-kit/plugins/core/AGENTS.md" "$agents_link"
if ! env HOME="$TEST_HOME" PATH="$RESTRICTED_PATH" AI_KIT_DIR="$TEST_HOME/.ai-kit" \
    "$TEST_HOME/.ai-kit/platforms/tools/doctor.sh" >"$ROOT/doctor-repoint-core.out" 2>&1; then
  cat "$ROOT/doctor-repoint-core.out" >&2
  fail "doctor failed to repoint the former plugins/core AGENTS.md symlink"
fi
[[ "$(readlink "$agents_link")" == "$TEST_HOME/.ai-kit/plugins/guardrails/AGENTS.md" ]] \
  || fail "former plugins/core AGENTS.md symlink was not repointed (KIT-055)"

if ! env HOME="$TEST_HOME" PATH="$RESTRICTED_PATH" AI_KIT_DIR="$TEST_HOME/.ai-kit" \
    "$TEST_HOME/.ai-kit/platforms/tools/doctor.sh" >"$ROOT/doctor-initial.out" 2>&1; then
  cat "$ROOT/doctor-initial.out" >&2
  fail "doctor failed after bootstrap"
fi
grep -Fq 'ok: kit clone at release v0.0.0' "$ROOT/doctor-initial.out" || fail "doctor did not report the release"

if [[ "$MODE" == --main ]]; then
  printf 'smoke: main path OK (bootstrap, Codex AGENTS.md link and its repoints, doctor)\n'
  exit 0
fi

if [[ "${OSTYPE:-}" == darwin* ]]; then
  # KIT-022: the rendered plist puts ~/.local/bin on launchd's PATH. A stub launchctl first on PATH
  # records the calls, so the machine's real ai-kit.refresh agent is never booted out or replaced.
  LAUNCHCTL_BIN="$ROOT/launchctl-bin"
  mkdir -p "$LAUNCHCTL_BIN"
  printf '#!/bin/sh\necho "$*" >> "%s/launchctl.calls"\n' "$ROOT" > "$LAUNCHCTL_BIN/launchctl"
  chmod +x "$LAUNCHCTL_BIN/launchctl"
  if ! env HOME="$TEST_HOME" PATH="$LAUNCHCTL_BIN:$RESTRICTED_PATH" \
      AI_KIT_DIR="$TEST_HOME/.ai-kit" AI_KIT_SOURCE="$SOURCE" AI_KIT_NO_LAUNCHD=0 \
      "$KIT_DIR/platforms/tools/bootstrap.sh" >"$ROOT/bootstrap-launchd.out" 2>&1; then
    cat "$ROOT/bootstrap-launchd.out" >&2
    fail "bootstrap failed to install the launchd refresh"
  fi
  plist="$TEST_HOME/Library/LaunchAgents/ai-kit.refresh.plist"
  plutil -lint "$plist" >/dev/null || fail "rendered launchd plist is not valid"
  grep -q '@[A-Z]*@' "$plist" && fail "rendered launchd plist keeps a placeholder"
  grep -Fq "<string>$TEST_HOME/.local/bin:/opt/homebrew/bin:" "$plist" \
    || fail "rendered launchd PATH does not start with ~/.local/bin"
  grep -Fq "<string>$TEST_HOME/.ai-kit/platforms/tools/refresh.sh</string>" "$plist" \
    || fail "rendered launchd plist does not run the kit's refresh.sh"
  grep -Fq "bootstrap gui/" "$ROOT/launchctl.calls" || fail "bootstrap did not load the rendered plist"
fi

mkdir -p "$TEST_HOME/.config/devin" \
  "$TEST_HOME/.agents/skills/kitone" \
  "$TEST_HOME/.agents/skills/my-own" \
  "$TEST_HOME/.config/agent-rules-kit"
printf '# Global Rules — AI Kit\n' > "$TEST_HOME/.config/devin/AGENTS.md"
printf 'marker\n' > "$TEST_HOME/.agents/skills/kitone/.agent-rules-kit"
printf '%s\n' '---' 'name: kitone' 'description: managed' '---' > "$TEST_HOME/.agents/skills/kitone/SKILL.md"
printf '%s\n' '---' 'name: my-own' 'description: user content' '---' > "$TEST_HOME/.agents/skills/my-own/SKILL.md"
printf 'old\n' > "$TEST_HOME/.config/agent-rules-kit/VERSION"

if ! env HOME="$TEST_HOME" PATH="$RESTRICTED_PATH" AI_KIT_DIR="$TEST_HOME/.ai-kit" \
    "$TEST_HOME/.ai-kit/platforms/tools/doctor.sh" >"$ROOT/doctor-cleanup.out" 2>&1; then
  cat "$ROOT/doctor-cleanup.out" >&2
  fail "doctor failed during legacy cleanup"
fi

[[ ! -e "$TEST_HOME/.config/devin/AGENTS.md" ]] || fail "legacy Devin AGENTS.md survived"
[[ ! -e "$TEST_HOME/.agents/skills/kitone" ]] || fail "marked kit skill survived"
[[ ! -e "$TEST_HOME/.config/agent-rules-kit" ]] || fail "legacy state survived"
[[ -f "$TEST_HOME/.agents/skills/my-own/SKILL.md" ]] || fail "unmarked user skill was removed"

printf '%s\n' '{"version":1,"extra":{"keep":true},"read_config_from":{"claude":false,"cursor":true}}' \
  > "$TEST_HOME/.config/devin/config.json"
if ! env HOME="$TEST_HOME" PATH="$RESTRICTED_PATH" AI_KIT_DIR="$TEST_HOME/.ai-kit" \
    "$TEST_HOME/.ai-kit/platforms/tools/doctor.sh" >"$ROOT/doctor-devin-config-merge.out" 2>&1; then
  cat "$ROOT/doctor-devin-config-merge.out" >&2
  fail "doctor failed to merge Devin imports"
fi
grep -Fq 'fix: devin read_config_from ' "$ROOT/doctor-devin-config-merge.out" \
  || fail "Devin import merge was not reported"
python3 - "$TEST_HOME/.config/devin/config.json" <<'PY'
import json
import sys
from pathlib import Path

path = Path(sys.argv[1])
data = json.loads(path.read_text(encoding="utf-8"))
assert data["version"] == 1
assert data["extra"] == {"keep": True}
assert data["read_config_from"] == {
    "agents_standard": True,
    "cursor": False,
    "windsurf": False,
    "claude": False,
    "copilot": False,
    "opencode": False,
    "zed": False,
}
assert path.read_text(encoding="utf-8").endswith("\n")
PY
cp "$TEST_HOME/.config/devin/config.json" "$ROOT/devin-config-before"
if ! env HOME="$TEST_HOME" PATH="$RESTRICTED_PATH" AI_KIT_DIR="$TEST_HOME/.ai-kit" \
    "$TEST_HOME/.ai-kit/platforms/tools/doctor.sh" >"$ROOT/doctor-devin-config-ok.out" 2>&1; then
  cat "$ROOT/doctor-devin-config-ok.out" >&2
  fail "doctor failed with narrowed Devin imports"
fi
grep -Fq 'ok: devin read_config_from limited to agents_standard' "$ROOT/doctor-devin-config-ok.out" \
  || fail "narrowed Devin imports were not reported"
cmp -s "$ROOT/devin-config-before" "$TEST_HOME/.config/devin/config.json" \
  || fail "Devin config merge was not idempotent"

FOREIGN_HOME="$ROOT/foreign-home"
mkdir -p "$FOREIGN_HOME/.codex"
git clone "$SOURCE" "$FOREIGN_HOME/.ai-kit" >/dev/null 2>&1
printf 'user-owned instructions\n' > "$FOREIGN_HOME/.codex/AGENTS.md"
cp "$FOREIGN_HOME/.codex/AGENTS.md" "$ROOT/foreign-before"
if env HOME="$FOREIGN_HOME" PATH="$RESTRICTED_PATH" AI_KIT_DIR="$FOREIGN_HOME/.ai-kit" \
    "$FOREIGN_HOME/.ai-kit/platforms/tools/doctor.sh" >"$ROOT/doctor-foreign.out" 2>&1; then
  fail "doctor accepted a foreign Codex AGENTS.md"
fi
grep -q '^FAIL:' "$ROOT/doctor-foreign.out" || fail "foreign-file failure was not reported"
cmp -s "$ROOT/foreign-before" "$FOREIGN_HOME/.codex/AGENTS.md" || fail "foreign Codex AGENTS.md changed"

APP_HOME="$ROOT/app-home"
mkdir -p "$APP_HOME/.codex/skills/investigate"
git clone "$SOURCE" "$APP_HOME/.ai-kit" >/dev/null 2>&1
touch "$APP_HOME/.codex/config.toml"
touch "$APP_HOME/.codex/skills/investigate/.agent-rules-kit"
if ! env HOME="$APP_HOME" PATH="$RESTRICTED_PATH" AI_KIT_DIR="$APP_HOME/.ai-kit" \
    "$APP_HOME/.ai-kit/platforms/tools/doctor.sh" >"$ROOT/doctor-app.out" 2>&1; then
  cat "$ROOT/doctor-app.out" >&2
  fail "doctor failed in Codex app-only mode"
fi
grep -Fq 'ok: codex CLI not found; desktop app detected — fallback symlinks maintained (openai/codex#22078)' \
  "$ROOT/doctor-app.out" || fail "app-only mode was not reported"
app_skill_count="$(find "$APP_HOME/.ai-kit"/plugins/*/skills -mindepth 1 -maxdepth 1 -type d 2>/dev/null | wc -l | tr -d ' ')"
fallback_count=0
for skill_file in "$APP_HOME/.ai-kit"/plugins/*/skills/*/SKILL.md; do
  [[ -f "$skill_file" ]] || continue
  name="$(basename "$(dirname "$skill_file")")"
  fallback="$APP_HOME/.codex/skills/$name"
  expected="$(dirname "$skill_file")"
  [[ -L "$fallback" ]] || fail "app-only fallback missing for $name"
  [[ "$(readlink "$fallback")" == "$expected" ]] || fail "app-only fallback for $name has the wrong target"
  fallback_count=$((fallback_count + 1))
done
[[ "$fallback_count" == "$app_skill_count" ]] || fail "$fallback_count app-only fallbacks, expected $app_skill_count"

if ! env HOME="$APP_HOME" PATH="$RESTRICTED_PATH" AI_KIT_DIR="$APP_HOME/.ai-kit" \
    "$APP_HOME/.ai-kit/platforms/tools/doctor.sh" >"$ROOT/doctor-app-second.out" 2>&1; then
  cat "$ROOT/doctor-app-second.out" >&2
  fail "second app-only doctor run failed"
fi
if grep -q '^fix:' "$ROOT/doctor-app-second.out"; then
  cat "$ROOT/doctor-app-second.out" >&2
  fail "second app-only doctor run was not idempotent"
fi

STUB_BIN="$ROOT/bin"
STUB_STATE="$ROOT/stub-state"
STUB_HOME="$ROOT/stub-home"
mkdir -p "$STUB_BIN" "$STUB_STATE" "$STUB_HOME"
cat > "$STUB_BIN/codex" <<'STUB'
#!/usr/bin/env bash
set -euo pipefail
state="${STUB_STATE_DIR:?}"
case "$*" in
  --version)
    echo "codex-cli 0.158.0-alpha.2.1"
    ;;
  "plugin marketplace list")
    if [[ "${STUB_MARKETPLACE:-0}" == "1" || -f "$state/marketplace" ]]; then
      echo "ai-kit ChristianPrzybulinski/agent-rules-kit"
    fi
    ;;
  "plugin list")
    if [[ "${STUB_PLUGIN:-0}" == "1" ]]; then
      echo "guardrails@ai-kit installed, enabled"
    elif [[ "${STUB_MARKETPLACE:-0}" == "1" || -f "$state/marketplace" ]]; then
      # Like the real CLI, every marketplace plugin is listed, "not installed" ones included (KIT-055)
      for plugin_dir in "$HOME/.ai-kit"/plugins/*/; do
        name="$(basename "$plugin_dir")"
        if [[ -f "$state/plugins/$name" ]]; then
          echo "$name@ai-kit  installed, enabled"
        else
          echo "$name@ai-kit  not installed"
        fi
      done
    fi
    ;;
  "plugin marketplace add "*" --ref "*)
    touch "$state/marketplace"
    python3 - "$HOME/.codex/config.toml" "$6" <<'PY'
import sys
from pathlib import Path

config = Path(sys.argv[1])
config.parent.mkdir(parents=True, exist_ok=True)
text = config.read_text(encoding="utf-8") if config.is_file() else ""
config.write_text(text + f'\n[marketplaces.ai-kit]\nsource_type = "git"\nref = "{sys.argv[2]}"\n', encoding="utf-8")
PY
    echo "Added marketplace ai-kit"
    ;;
  "plugin marketplace remove ai-kit")
    rm -f "$state/marketplace"
    python3 - "$HOME/.codex/config.toml" <<'PY'
import sys
from pathlib import Path

config = Path(sys.argv[1])
kept, skipping = [], False
for line in config.read_text(encoding="utf-8").splitlines():
    if line.startswith("["):
        skipping = line.strip() == "[marketplaces.ai-kit]"
    if not skipping:
        kept.append(line)
config.write_text("\n".join(kept) + "\n", encoding="utf-8")
PY
    echo "Removed marketplace ai-kit"
    ;;
  "plugin add "*@ai-kit)
    mkdir -p "$state/plugins"
    name="${3%@ai-kit}"
    touch "$state/plugins/$name"
    echo "Added plugin $name from marketplace ai-kit."
    ;;
  "plugin remove "*@ai-kit)
    name="${3%@ai-kit}"
    python3 - "$HOME/.codex/config.toml" "$name@ai-kit" <<'PY'
import sys
from pathlib import Path

config = Path(sys.argv[1])
header = f'[plugins."{sys.argv[2]}"]'
kept = []
skipping = False
for line in config.read_text(encoding="utf-8").splitlines():
    if line.startswith("["):
        skipping = line.strip() == header
    if not skipping:
        kept.append(line)
config.write_text("\n".join(kept) + "\n", encoding="utf-8")
PY
    mkdir -p "$state/codex-removed"
    touch "$state/codex-removed/$name"
    echo "Removed plugin $name from marketplace ai-kit."
    ;;
  "plugin marketplace upgrade ai-kit")
    touch "$state/upgrade"
    echo "Upgraded marketplace ai-kit"
    ;;
  "debug prompt-input list skills")
    count="${STUB_EXPOSED:-0}"
    for ((i = 1; i <= count; i++)); do
      echo "guardrails:x$i"
    done
    ;;
  *)
    echo "unexpected codex stub arguments: $*" >&2
    exit 2
    ;;
esac
STUB
chmod +x "$STUB_BIN/codex"
cat > "$STUB_BIN/claude" <<'STUB'
#!/usr/bin/env bash
set -euo pipefail
state="${STUB_STATE_DIR:?}"
case "$*" in
  "plugin marketplace list --json")
    if [[ -f "$state/claude-marketplace" ]]; then
      printf '[{"name":"ai-kit","installLocation":"%s"}]\n' "$HOME/.ai-kit"
    else
      echo '[]'
    fi
    ;;
  "plugin marketplace add ChristianPrzybulinski/agent-rules-kit#stable --json")
    touch "$state/claude-marketplace"
    # KIT-081: Claude Code 2.1.287 records the source, ref included, in known_marketplaces.json
    mkdir -p "$HOME/.claude/plugins"
    printf '{"ai-kit": {"source": {"source": "github", "repo": "ChristianPrzybulinski/agent-rules-kit", "ref": "stable"}}}\n' \
      > "$HOME/.claude/plugins/known_marketplaces.json"
    echo '{"name":"ai-kit"}'
    ;;
  "plugin list --json")
    if [[ -d "$state/claude-plugins" ]]; then
      printf '['
      first=1
      for installed in "$state/claude-plugins"/*; do
        [[ -f "$installed" ]] || continue
        [[ "$first" -eq 0 ]] && printf ','
        first=0
        name="$(basename "$installed")"
        printf '{"id":"%s@ai-kit","scope":"user","installPath":"%s"}' "$name" "$state/claude-cache/$name"
      done
      printf ']\n'
    else
      echo '[]'
    fi
    ;;
  "plugin install "*@ai-kit" --json")
    mkdir -p "$state/claude-plugins"
    name="${3%@ai-kit}"
    touch "$state/claude-plugins/$name"
    mkdir -p "$state/claude-cache"
    cp -R "$HOME/.ai-kit/plugins/$name" "$state/claude-cache/$name"
    mkdir -p "$state/claude-cache/$name/.in_use"
    touch "$state/claude-cache/$name/.in_use/4242"
    printf '{"id":"%s@ai-kit"}\n' "$name"
    ;;
  "plugin uninstall "*@ai-kit" --keep-data --json")
    name="${3%@ai-kit}"
    rm -rf "$state/claude-cache/$name"
    rm -f "$state/claude-plugins/$name"
    mkdir -p "$state/claude-uninstalls"
    touch "$state/claude-uninstalls/$name"
    printf '{"id":"%s@ai-kit"}\n' "$name"
    ;;
  "plugin marketplace update ai-kit --json")
    touch "$state/claude-marketplace-update"
    echo '{"name":"ai-kit"}'
    ;;
  "plugin update "*@ai-kit" --json")
    mkdir -p "$state/claude-plugin-updates"
    name="${3%@ai-kit}"
    touch "$state/claude-plugin-updates/$name"
    printf '{"id":"%s@ai-kit"}\n' "$name"
    ;;
  *)
    echo "unexpected claude stub arguments: $*" >&2
    exit 2
    ;;
esac
STUB
chmod +x "$STUB_BIN/claude"
git clone "$SOURCE" "$STUB_HOME/.ai-kit" >/dev/null 2>&1
# KIT-055: a plugin the kit renamed stays enabled in config.toml until the doctor removes it.
mkdir -p "$STUB_HOME/.codex"
printf '[plugins."core@ai-kit"]\nenabled = true\n\n[plugins."other@elsewhere"]\nenabled = true\n' \
  > "$STUB_HOME/.codex/config.toml"

stub_path="$STUB_BIN:$RESTRICTED_PATH"
if ! env HOME="$STUB_HOME" PATH="$stub_path" AI_KIT_NO_CODEX_CLI=0 \
    AI_KIT_DIR="$STUB_HOME/.ai-kit" STUB_STATE_DIR="$STUB_STATE" STUB_EXPOSED=43 \
    AI_KIT_USER_RULES=1 \
    "$STUB_HOME/.ai-kit/platforms/tools/doctor.sh" >"$ROOT/doctor-stub-install.out" 2>&1; then
  cat "$ROOT/doctor-stub-install.out" >&2
  fail "doctor failed to install stub marketplace/plugin"
fi
grep -Fq 'fix: codex marketplace ai-kit registered' "$ROOT/doctor-stub-install.out" \
  || fail "stub marketplace add was not reported"
grep -Fq 'fix: codex plugin core@ai-kit removed (no longer in the kit)' "$ROOT/doctor-stub-install.out" \
  || fail "retired Codex plugin removal was not reported (KIT-055)"
[[ -f "$STUB_STATE/codex-removed/core" ]] || fail "doctor did not run codex plugin remove core@ai-kit"
grep -Fq '[plugins."core@ai-kit"]' "$STUB_HOME/.codex/config.toml" \
  && fail "retired Codex plugin table remained in config.toml"
grep -Fq '[plugins."other@elsewhere"]' "$STUB_HOME/.codex/config.toml" \
  || fail "doctor removed a plugin from another marketplace"
codex_fixes="$(grep -c 'fix: codex plugin .*@ai-kit installed' "$ROOT/doctor-stub-install.out" || true)"
plugin_total="$(find "$STUB_HOME/.ai-kit"/plugins -mindepth 1 -maxdepth 1 -type d | wc -l | tr -d ' ')"
[[ "$codex_fixes" == "$plugin_total" ]] \
  || fail "$codex_fixes codex plugin installs reported, expected $plugin_total"
grep -Fq 'ok: codex plugin exposes 43 kit skills' "$ROOT/doctor-stub-install.out" \
  || fail "stub exposed-skill count was not reported"
grep -Fq 'fix: claude marketplace ai-kit registered' "$ROOT/doctor-stub-install.out" \
  || fail "Claude marketplace add was not reported"
claude_fixes="$(grep -c 'fix: claude plugin .*@ai-kit installed' "$ROOT/doctor-stub-install.out" || true)"
[[ "$claude_fixes" == "$plugin_total" ]] \
  || fail "$claude_fixes Claude plugin installs reported, expected $plugin_total"
for plugin_dir in "$STUB_HOME/.ai-kit"/plugins/*/; do
  [[ -f "$STUB_STATE/claude-plugins/$(basename "$plugin_dir")" ]] \
    || fail "Claude stub install marker missing for $(basename "$plugin_dir")"
done
[[ -f "$STUB_STATE/claude-marketplace" ]] || fail "Claude stub marketplace marker missing"
[[ "$(readlink "$STUB_HOME/.claude/CLAUDE.md")" == "$STUB_HOME/.ai-kit/plugins/guardrails/AGENTS.md" ]] \
  || fail "Claude CLAUDE.md symlink has the wrong target"
grep -Fq "fix: claude autoCompactWindow set to 300000 in $STUB_HOME/.claude/settings.json (KIT-010)" \
  "$ROOT/doctor-stub-install.out" || fail "autoCompactWindow fix was not reported"
[[ "$(stub_compact_window)" == "300000" ]] || fail "autoCompactWindow was not written as the number 300000"
for rule_file in "$STUB_HOME/.ai-kit"/plugins/*/rules/*.md; do
  [[ -f "$rule_file" ]] || continue
  plugin_name="$(dirname "$(dirname "$rule_file")")"
  plugin_name="$(basename "$plugin_name")"
  rule_name="${rule_file##*/}"
  rule_name="${rule_name%.md}"
  [[ "$(readlink "$STUB_HOME/.claude/rules/$plugin_name-$rule_name.md")" == "$rule_file" ]] \
    || fail "Claude rule symlink has the wrong target for $plugin_name-$rule_name"
done

if ! env HOME="$STUB_HOME" PATH="$stub_path" AI_KIT_NO_CODEX_CLI=0 \
    AI_KIT_DIR="$STUB_HOME/.ai-kit" STUB_STATE_DIR="$STUB_STATE" STUB_EXPOSED=43 \
    "$STUB_HOME/.ai-kit/platforms/tools/doctor.sh" >"$ROOT/doctor-stub-no-user-rules.out" 2>&1; then
  cat "$ROOT/doctor-stub-no-user-rules.out" >&2
  fail "doctor failed with the default AI_KIT_USER_RULES (0)"
fi
grep -Fq 'ok: user-level claude rules disabled (AI_KIT_USER_RULES=0); repos carry .claude/rules via sync-project.sh' \
  "$ROOT/doctor-stub-no-user-rules.out" || fail "AI_KIT_USER_RULES=0 switch was not reported"
[[ "$(find "$STUB_HOME/.claude/rules" -type l | wc -l | tr -d ' ')" == "0" ]] \
  || fail "user-level rule symlinks remained under AI_KIT_USER_RULES=0"
grep -Fq 'ok: claude autoCompactWindow 300000' "$ROOT/doctor-stub-no-user-rules.out" \
  || fail "autoCompactWindow 300000 was not reported ok on the second run"

# KIT-010: an explicit owner value above the kit's window is kept and reported, never overwritten.
set_stub_compact_window 500000

if ! env HOME="$STUB_HOME" PATH="$stub_path" AI_KIT_NO_CODEX_CLI=0 \
    AI_KIT_DIR="$STUB_HOME/.ai-kit" STUB_STATE_DIR="$STUB_STATE" STUB_EXPOSED=43 \
    AI_KIT_USER_RULES=1 \
    "$STUB_HOME/.ai-kit/platforms/tools/doctor.sh" >"$ROOT/doctor-stub-user-rules.out" 2>&1; then
  cat "$ROOT/doctor-stub-user-rules.out" >&2
  fail "doctor failed to restore user-level rule symlinks"
fi
grep -Fq "warn: claude autoCompactWindow 500000 is above the kit's 300000 — kept (owner's choice)" \
  "$ROOT/doctor-stub-user-rules.out" || fail "an owner autoCompactWindow above 300000 was not reported"
[[ "$(stub_compact_window)" == "500000" ]] || fail "doctor overwrote the owner's autoCompactWindow"
for rule_file in "$STUB_HOME/.ai-kit"/plugins/*/rules/*.md; do
  [[ -f "$rule_file" ]] || continue
  plugin_name="$(dirname "$(dirname "$rule_file")")"
  plugin_name="$(basename "$plugin_name")"
  rule_name="${rule_file##*/}"
  rule_name="${rule_name%.md}"
  [[ "$(readlink "$STUB_HOME/.claude/rules/$plugin_name-$rule_name.md")" == "$rule_file" ]] \
    || fail "user-level rule symlink was not restored for $plugin_name-$rule_name"
done

stub_fallback_count=0
if [[ -d "$STUB_HOME/.codex/skills" ]]; then
  stub_fallback_count="$(find "$STUB_HOME/.codex/skills" -type l | wc -l | tr -d ' ')"
fi
[[ "$stub_fallback_count" == "0" ]] || fail "fallback created despite exposed stub skills"

# KIT-010: the string "200k" an older doctor wrote was never applied by Claude Code; the doctor replaces it.
set_stub_compact_window '"200k"'
if ! env HOME="$STUB_HOME" PATH="$stub_path" AI_KIT_NO_CODEX_CLI=0 \
    AI_KIT_DIR="$STUB_HOME/.ai-kit" STUB_STATE_DIR="$STUB_STATE" STUB_EXPOSED=0 \
    "$STUB_HOME/.ai-kit/platforms/tools/doctor.sh" >"$ROOT/doctor-stub-fallback.out" 2>&1; then
  cat "$ROOT/doctor-stub-fallback.out" >&2
  fail "doctor failed to create stub fallback"
fi
grep -Fq "fix: claude autoCompactWindow \"200k\", a string Claude Code ignores, replaced by 300000 in $STUB_HOME/.claude/settings.json (KIT-010)" \
  "$ROOT/doctor-stub-fallback.out" || fail "the legacy autoCompactWindow \"200k\" was not reported as replaced"
[[ "$(stub_compact_window)" == "300000" ]] || fail "the legacy autoCompactWindow \"200k\" was not replaced by 300000"
stub_skill_count="$(find "$STUB_HOME/.ai-kit"/plugins/*/skills -mindepth 1 -maxdepth 1 -type d 2>/dev/null | wc -l | tr -d ' ')"
stub_fallback_count="$(find "$STUB_HOME/.codex/skills" -type l | wc -l | tr -d ' ')"
[[ "$stub_fallback_count" == "$stub_skill_count" ]] \
  || fail "$stub_fallback_count stub fallbacks, expected $stub_skill_count"

# KIT-010: any other value Claude Code drops (here an owner's "500k") is kept and reported as ignored.
set_stub_compact_window '"500k"'
if ! env HOME="$STUB_HOME" PATH="$stub_path" AI_KIT_NO_CODEX_CLI=0 \
    AI_KIT_DIR="$STUB_HOME/.ai-kit" STUB_STATE_DIR="$STUB_STATE" STUB_EXPOSED=43 \
    "$STUB_HOME/.ai-kit/platforms/tools/doctor.sh" >"$ROOT/doctor-stub-remove.out" 2>&1; then
  cat "$ROOT/doctor-stub-remove.out" >&2
  fail "doctor failed to remove stub fallback"
fi
grep -Fq 'warn: claude autoCompactWindow "500k" is not an integer from 100000 to 1000000, so Claude Code ignores it — kept; write a number such as 300000' \
  "$ROOT/doctor-stub-remove.out" || fail "an autoCompactWindow Claude Code ignores was not reported"
[[ "$(stub_compact_window)" == '"500k"' ]] || fail "doctor overwrote an owner autoCompactWindow it does not recognize"
stub_fallback_count="$(find "$STUB_HOME/.codex/skills" -type l | wc -l | tr -d ' ')"
[[ "$stub_fallback_count" == "0" ]] || fail "stub fallback remained after plugin exposure"
grep -Fq 'ok: codex plugin exposes 43 kit skills' "$ROOT/doctor-stub-remove.out" \
  || fail "stub re-exposure count was not reported"

# KIT-081 stage 2b: a checkout Claude Code records that still holds the retired vendored kit state is reported with
# the sync that removes it; a plugins-mode checkout and a kit-marked folder's lookalike without the marker are not.
for proj in marked manifest plain own; do
  mkdir -p "$ROOT/vend-$proj/.claude/skills"
done
mkdir -p "$ROOT/vend-marked/.claude/skills/investigate" "$ROOT/vend-own/.claude/skills/investigate"
printf 'plugins/guardrails/skills/investigate kit 13.1.0 generated by platforms/tools/sync-project.sh; do not edit\n' \
  > "$ROOT/vend-marked/.claude/skills/investigate/.agent-rules-kit"
printf '{"profile": "docs"}\n' > "$ROOT/vend-manifest/.claude/skills/KIT_MANIFEST.json"
printf '{"enabledPlugins": {"guardrails@ai-kit": true}}\n' > "$ROOT/vend-plain/.claude/settings.json"
mkdir -p "$STUB_HOME/.claude/plugins"
cat > "$STUB_HOME/.claude/plugins/installed_plugins.json" <<EOF
{"version": 2, "plugins": {"guardrails@ai-kit": [
  {"scope": "project", "projectPath": "$ROOT/vend-marked"},
  {"scope": "local", "projectPath": "$ROOT/vend-marked"},
  {"scope": "project", "projectPath": "$ROOT/vend-manifest"},
  {"scope": "project", "projectPath": "$ROOT/vend-plain"},
  {"scope": "project", "projectPath": "$ROOT/vend-own"},
  {"scope": "project", "projectPath": "$ROOT/vend-gone"},
  {"scope": "user"}]}}
EOF
if ! env HOME="$STUB_HOME" PATH="$stub_path" AI_KIT_NO_CODEX_CLI=0 \
    AI_KIT_DIR="$STUB_HOME/.ai-kit" STUB_STATE_DIR="$STUB_STATE" STUB_EXPOSED=43 \
    "$STUB_HOME/.ai-kit/platforms/tools/doctor.sh" >"$ROOT/doctor-stub-vendored.out" 2>&1; then
  cat "$ROOT/doctor-stub-vendored.out" >&2
  fail "doctor failed with vendored and plugins-mode checkouts"
fi
grep -Fq "warn: claude: 2 checkouts still hold the vendored kit state KIT-081 stage 2b removed: $ROOT/vend-manifest, $ROOT/vend-marked — run platforms/tools/sync-project.sh <repo> in each once" \
  "$ROOT/doctor-stub-vendored.out" || fail "doctor did not report the checkouts that still hold vendored kit state"
! grep -Eq 'vend-(plain|own|gone)' "$ROOT/doctor-stub-vendored.out" \
  || fail "doctor reported a checkout without vendored kit state"
rm -f "$STUB_HOME/.claude/plugins/installed_plugins.json"

# KIT-013: a cache that differs from the kit without a version bump is reported, then reinstalled.
printf 'stale\n' >> "$STUB_STATE/claude-cache/guardrails/INDEX.md"
if ! env HOME="$STUB_HOME" PATH="$stub_path" AI_KIT_NO_CODEX_CLI=0 \
    AI_KIT_DIR="$STUB_HOME/.ai-kit" STUB_STATE_DIR="$STUB_STATE" STUB_EXPOSED=43 \
    "$STUB_HOME/.ai-kit/platforms/tools/doctor.sh" >"$ROOT/doctor-stub-stale.out" 2>&1; then
  cat "$ROOT/doctor-stub-stale.out" >&2
  fail "doctor failed with a stale Claude plugin cache"
fi
grep -Fq 'warn: claude plugin guardrails@ai-kit cache differs from the kit — run platforms/tools/refresh.sh' \
  "$ROOT/doctor-stub-stale.out" || fail "doctor did not warn about the stale Claude plugin cache"

if ! env HOME="$STUB_HOME" PATH="$stub_path" AI_KIT_NO_CODEX_CLI=0 \
    AI_KIT_DIR="$STUB_HOME/.ai-kit" STUB_STATE_DIR="$STUB_STATE" \
    "$STUB_HOME/.ai-kit/platforms/tools/refresh.sh" >"$ROOT/refresh-stub.out" 2>&1; then
  cat "$ROOT/refresh-stub.out" >&2
  fail "refresh failed with registered stub marketplace"
fi
[[ -f "$STUB_STATE/upgrade" ]] || fail "refresh did not upgrade the stub marketplace"
[[ -f "$STUB_STATE/claude-marketplace-update" ]] || fail "refresh did not update the Claude marketplace"
[[ -f "$STUB_STATE/claude-plugin-updates/guardrails" ]] || fail "refresh did not update the Claude guardrails plugin"
[[ -f "$STUB_STATE/claude-uninstalls/guardrails" && -f "$STUB_STATE/claude-plugins/guardrails" ]] \
  || fail "refresh did not reinstall the stale Claude guardrails plugin"
grep -Fq 'refresh: reinstalled Claude plugin guardrails@ai-kit (cache differed from the kit)' "$ROOT/refresh-stub.out" \
  || fail "refresh did not report the Claude reinstall"
diff -rq -x .in_use "$STUB_HOME/.ai-kit/plugins/guardrails" "$STUB_STATE/claude-cache/guardrails" >/dev/null \
  || fail "reinstalled Claude cache still differs from the kit"
# KIT-056: refresh runs the cross-session audit pre-filter, which prints counts only, then waits 7 days.
grep -Fq '{"ran": 1,' "$ROOT/refresh-stub.out" || fail "refresh did not run session_audit.py"
[[ "$(python3 -c 'import os, sys; print(oct(os.stat(sys.argv[1]).st_mode & 0o777))' \
  "$STUB_HOME/.local/state/ai-kit/session-audit/last-run" 2>/dev/null)" == 0o600 ]] \
  || fail "session_audit.py did not write its stamp with mode 0600"

rm -rf "$STUB_STATE/claude-uninstalls"
if ! env HOME="$STUB_HOME" PATH="$stub_path" AI_KIT_NO_CODEX_CLI=0 \
    AI_KIT_DIR="$STUB_HOME/.ai-kit" STUB_STATE_DIR="$STUB_STATE" \
    "$STUB_HOME/.ai-kit/platforms/tools/refresh.sh" >"$ROOT/refresh-stub-current.out" 2>&1; then
  cat "$ROOT/refresh-stub-current.out" >&2
  fail "refresh failed with an up-to-date Claude plugin cache"
fi
[[ ! -e "$STUB_STATE/claude-uninstalls" ]] || fail "refresh reinstalled an up-to-date Claude plugin cache"
grep -Fq 'reinstalled' "$ROOT/refresh-stub-current.out" && fail "refresh reported a reinstall of an up-to-date cache"
grep -Fq 'running doctor.sh' "$ROOT/refresh-stub-current.out" && fail "refresh ran the doctor with no broken kit link"
grep -Fq '{"ran": 0,' "$ROOT/refresh-stub-current.out" || fail "refresh ran session_audit.py again within 7 days"

# #271, KIT-081: a Codex marketplace that still follows main moves to the stable branch, refresh and doctor alike, and
# each kit plugin is added again so its cache takes the branch's version.
set_codex_ref_main() {
  python3 - "$STUB_HOME/.codex/config.toml" <<'PY'
import sys
from pathlib import Path

config = Path(sys.argv[1])
config.write_text(config.read_text(encoding="utf-8").replace('ref = "stable"', 'ref = "main"'), encoding="utf-8")
PY
  grep -Fq 'ref = "main"' "$STUB_HOME/.codex/config.toml" || fail "the stub Codex config has no ai-kit ref to move"
  rm -f "$STUB_STATE/plugins/guardrails"
}
set_codex_ref_main
if ! env HOME="$STUB_HOME" PATH="$stub_path" AI_KIT_NO_CODEX_CLI=0 \
    AI_KIT_DIR="$STUB_HOME/.ai-kit" STUB_STATE_DIR="$STUB_STATE" \
    "$STUB_HOME/.ai-kit/platforms/tools/refresh.sh" >"$ROOT/refresh-stub-codex-ref.out" 2>&1; then
  cat "$ROOT/refresh-stub-codex-ref.out" >&2
  fail "refresh failed with a Codex marketplace on main"
fi
grep -Fq 'refresh: codex marketplace ai-kit moved from main to stable' "$ROOT/refresh-stub-codex-ref.out" \
  || fail "refresh did not move the Codex marketplace to the stable branch"
grep -Fq 'ref = "stable"' "$STUB_HOME/.codex/config.toml" || fail "refresh left the Codex marketplace off the stable branch"
[[ -f "$STUB_STATE/plugins/guardrails" ]] || fail "refresh did not add the kit plugin again at the stable branch"
set_codex_ref_main
if ! env HOME="$STUB_HOME" PATH="$stub_path" AI_KIT_NO_CODEX_CLI=0 \
    AI_KIT_DIR="$STUB_HOME/.ai-kit" STUB_STATE_DIR="$STUB_STATE" STUB_EXPOSED=43 \
    "$STUB_HOME/.ai-kit/platforms/tools/doctor.sh" >"$ROOT/doctor-stub-codex-ref.out" 2>&1; then
  cat "$ROOT/doctor-stub-codex-ref.out" >&2
  fail "doctor failed with a Codex marketplace on main"
fi
grep -Fq 'fix: codex marketplace ai-kit moved from main to stable' "$ROOT/doctor-stub-codex-ref.out" \
  || fail "doctor did not move the Codex marketplace to the stable branch"
grep -Fq 'fix: codex plugin guardrails@ai-kit installed' "$ROOT/doctor-stub-codex-ref.out" \
  || fail "doctor did not add the kit plugin again at the stable branch"

# KIT-055: an installed <name>@ai-kit that the kit no longer ships is reported with its remedy.
touch "$STUB_STATE/claude-plugins/core"
if ! env HOME="$STUB_HOME" PATH="$stub_path" AI_KIT_NO_CODEX_CLI=0 \
    AI_KIT_DIR="$STUB_HOME/.ai-kit" STUB_STATE_DIR="$STUB_STATE" STUB_EXPOSED=43 \
    "$STUB_HOME/.ai-kit/platforms/tools/doctor.sh" >"$ROOT/doctor-stub-retired.out" 2>&1; then
  cat "$ROOT/doctor-stub-retired.out" >&2
  fail "doctor failed with a retired Claude plugin installed"
fi
grep -Fq 'warn: claude plugin core@ai-kit is no longer in the kit (scope: user) — user scope: claude plugin uninstall core@ai-kit; project scope: run platforms/tools/sync-project.sh in that repository' \
  "$ROOT/doctor-stub-retired.out" || fail "doctor did not warn about the retired Claude plugin"
grep -Fq 'warn: claude plugin guardrails@ai-kit is no longer' "$ROOT/doctor-stub-retired.out" \
  && fail "doctor reported a current kit plugin as retired"
rm -f "$STUB_STATE/claude-plugins/core"

# KIT-055: a pull that renames a kit path leaves the always-on link dangling; refresh runs the doctor once.
ln -sfn "$STUB_HOME/.ai-kit/plugins/core/AGENTS.md" "$STUB_HOME/.claude/CLAUDE.md"
if ! env HOME="$STUB_HOME" PATH="$stub_path" AI_KIT_NO_CODEX_CLI=0 \
    AI_KIT_DIR="$STUB_HOME/.ai-kit" STUB_STATE_DIR="$STUB_STATE" STUB_EXPOSED=43 \
    "$STUB_HOME/.ai-kit/platforms/tools/refresh.sh" >"$ROOT/refresh-stub-dangling.out" 2>&1; then
  cat "$ROOT/refresh-stub-dangling.out" >&2
  fail "refresh failed with a dangling kit link"
fi
grep -Fq "refresh: kit link $STUB_HOME/.claude/CLAUDE.md is broken; running doctor.sh" \
  "$ROOT/refresh-stub-dangling.out" || fail "refresh did not report the dangling kit link"
[[ "$(readlink "$STUB_HOME/.claude/CLAUDE.md")" == "$STUB_HOME/.ai-kit/plugins/guardrails/AGENTS.md" ]] \
  || fail "refresh did not repair the dangling CLAUDE.md link"

# KIT-022: a CLI missing from PATH logs a skip line instead of passing in silence
if ! env HOME="$STUB_HOME" PATH="$RESTRICTED_PATH" AI_KIT_DIR="$STUB_HOME/.ai-kit" \
    "$STUB_HOME/.ai-kit/platforms/tools/refresh.sh" >"$ROOT/refresh-no-cli.out" 2>&1; then
  cat "$ROOT/refresh-no-cli.out" >&2
  fail "refresh failed without agent CLIs"
fi
grep -Fq 'skip: refresh: no codex CLI found; Codex marketplace not upgraded' "$ROOT/refresh-no-cli.out" \
  || fail "refresh did not log the missing codex CLI"
grep -Fq "skip: refresh: claude CLI not found on PATH $RESTRICTED_PATH; Claude plugins not updated" \
  "$ROOT/refresh-no-cli.out" || fail "refresh did not log the missing claude CLI"

# KIT-023: CODEX_BIN names a CLI that is not on PATH; a CODEX_BIN that is not executable finds none.
[[ "$(CODEX_BIN="$STUB_BIN/codex" AI_KIT_NO_CODEX_CLI=0 "$SOURCE/platforms/tools/codex-bin.sh")" == "$STUB_BIN/codex" ]] \
  || fail "codex-bin.sh did not print CODEX_BIN"
rm -f "$STUB_STATE/upgrade"
if ! env HOME="$STUB_HOME" PATH="$RESTRICTED_PATH" CODEX_BIN="$STUB_BIN/codex" AI_KIT_NO_CODEX_CLI=0 \
    AI_KIT_DIR="$STUB_HOME/.ai-kit" STUB_STATE_DIR="$STUB_STATE" \
    "$STUB_HOME/.ai-kit/platforms/tools/refresh.sh" >"$ROOT/refresh-codex-bin.out" 2>&1; then
  cat "$ROOT/refresh-codex-bin.out" >&2
  fail "refresh failed with CODEX_BIN"
fi
[[ -f "$STUB_STATE/upgrade" ]] || fail "refresh did not use the Codex CLI named by CODEX_BIN"
rm -f "$STUB_STATE/upgrade"
if ! env HOME="$STUB_HOME" PATH="$stub_path" CODEX_BIN="$ROOT/no-codex" AI_KIT_NO_CODEX_CLI=0 \
    AI_KIT_DIR="$STUB_HOME/.ai-kit" STUB_STATE_DIR="$STUB_STATE" \
    "$STUB_HOME/.ai-kit/platforms/tools/refresh.sh" >"$ROOT/refresh-codex-bin-missing.out" 2>&1; then
  cat "$ROOT/refresh-codex-bin-missing.out" >&2
  fail "refresh failed with a CODEX_BIN that does not exist"
fi
grep -Fq "WARN: CODEX_BIN=$ROOT/no-codex is not an executable file" "$ROOT/refresh-codex-bin-missing.out" \
  || fail "refresh did not warn about a CODEX_BIN that does not exist"
[[ ! -e "$STUB_STATE/upgrade" ]] || fail "refresh fell back to PATH despite an explicit CODEX_BIN"

# KIT-046: a pull that changes refresh.sh hands over once to the pulled script, in the same run.
REEXEC_HOME="$ROOT/reexec-home"
git clone "$SOURCE" "$ROOT/reexec-origin" >/dev/null 2>&1
git clone "$ROOT/reexec-origin" "$REEXEC_HOME/.ai-kit" >/dev/null 2>&1
cat >>"$ROOT/reexec-origin/platforms/tools/refresh.sh" <<'EOF'
printf 'smoke: pulled refresh.sh ran\n'
EOF
git -C "$ROOT/reexec-origin" -c maintenance.auto=false -c gc.auto=0 -c user.name=smoke \
  -c user.email=smoke@example.invalid commit -qam "smoke: change refresh.sh"
git -C "$ROOT/reexec-origin" tag v0.0.1
for run in changed current; do
  if ! env HOME="$REEXEC_HOME" PATH="$RESTRICTED_PATH" AI_KIT_DIR="$REEXEC_HOME/.ai-kit" \
      "$REEXEC_HOME/.ai-kit/platforms/tools/refresh.sh" >"$ROOT/refresh-reexec-$run.out" 2>&1; then
    cat "$ROOT/refresh-reexec-$run.out" >&2
    fail "refresh failed on the $run refresh.sh"
  fi
  [[ "$(grep -c 'smoke: pulled refresh.sh ran' "$ROOT/refresh-reexec-$run.out")" == 1 ]] \
    || fail "the pulled refresh.sh did not run exactly once ($run)"
done
[[ "$(grep -c 'refresh: the release changed refresh.sh; running the new version' "$ROOT/refresh-reexec-changed.out")" == 1 ]] \
  || fail "refresh did not hand over to the pulled refresh.sh"
grep -Fq 'running the new version' "$ROOT/refresh-reexec-current.out" \
  && fail "refresh handed over although the pull did not change refresh.sh"

# #271: a kit merge without a release changes nothing on the machine; the next tag moves the clone; a clone that
# follows main past the newest release is drift that doctor reports.
RELEASE_HOME="$ROOT/release-home"
git clone "$SOURCE" "$ROOT/release-origin" >/dev/null 2>&1
git clone "$ROOT/release-origin" "$RELEASE_HOME/.ai-kit" >/dev/null 2>&1
release_commit() {
  printf '%s\n' "$1" >> "$ROOT/release-origin/README.md"
  git -C "$ROOT/release-origin" -c maintenance.auto=false -c gc.auto=0 -c user.name=smoke \
    -c user.email=smoke@example.invalid commit -qam "smoke: $1"
}
release_refresh() {
  if ! env HOME="$RELEASE_HOME" PATH="$RESTRICTED_PATH" AI_KIT_DIR="$RELEASE_HOME/.ai-kit" \
      "$RELEASE_HOME/.ai-kit/platforms/tools/refresh.sh" >"$ROOT/refresh-release-$1.out" 2>&1; then
    cat "$ROOT/refresh-release-$1.out" >&2
    fail "refresh failed ($1)"
  fi
}
release_commit "merge without a release"
release_refresh unreleased
[[ "$(git -C "$RELEASE_HOME/.ai-kit" rev-parse HEAD)" == "$(git -C "$ROOT/release-origin" rev-parse 'v0.0.0^{commit}')" ]] \
  || fail "refresh moved the clone to an unreleased commit"
grep -Eq '^refresh: [0-9a-f]+ [0-9-]+ v0\.0\.0$' "$ROOT/refresh-release-unreleased.out" \
  || fail "refresh did not report the release it follows"
env HOME="$RELEASE_HOME" PATH="$RESTRICTED_PATH" AI_KIT_DIR="$RELEASE_HOME/.ai-kit" \
  "$RELEASE_HOME/.ai-kit/platforms/tools/doctor.sh" >"$ROOT/doctor-release-unreleased.out" 2>&1 || true
grep -Fq 'ok: kit clone at release v0.0.0' "$ROOT/doctor-release-unreleased.out" \
  || fail "doctor did not accept the release behind an unreleased merge"
git -C "$ROOT/release-origin" tag v0.0.1
release_refresh released
[[ "$(git -C "$RELEASE_HOME/.ai-kit" rev-parse HEAD)" == "$(git -C "$ROOT/release-origin" rev-parse 'v0.0.1^{commit}')" ]] \
  || fail "refresh did not move the clone to the new release"
release_commit "merge after the release"
git -C "$RELEASE_HOME/.ai-kit" fetch -q origin
git -C "$RELEASE_HOME/.ai-kit" checkout -q --detach origin/main
env HOME="$RELEASE_HOME" PATH="$RESTRICTED_PATH" AI_KIT_DIR="$RELEASE_HOME/.ai-kit" \
  "$RELEASE_HOME/.ai-kit/platforms/tools/doctor.sh" >"$ROOT/doctor-release-ahead.out" 2>&1 || true
grep -Fq 'FAIL: kit clone is not at the newest release v0.0.1 — run platforms/tools/refresh.sh' \
  "$ROOT/doctor-release-ahead.out" || fail "doctor did not report a clone past the newest release"

FOREIGN_LINK_HOME="$ROOT/foreign-link-home"
mkdir -p "$FOREIGN_LINK_HOME/.codex"
git clone "$SOURCE" "$FOREIGN_LINK_HOME/.ai-kit" >/dev/null 2>&1
ln -s /tmp/elsewhere.md "$FOREIGN_LINK_HOME/.codex/AGENTS.md"
if env HOME="$FOREIGN_LINK_HOME" PATH="$RESTRICTED_PATH" AI_KIT_DIR="$FOREIGN_LINK_HOME/.ai-kit" \
    "$FOREIGN_LINK_HOME/.ai-kit/platforms/tools/doctor.sh" >"$ROOT/doctor-foreign-link.out" 2>&1; then
  fail "doctor accepted a foreign Codex AGENTS.md symlink"
fi
grep -q '^FAIL:' "$ROOT/doctor-foreign-link.out" || fail "foreign-symlink failure was not reported"
[[ "$(readlink "$FOREIGN_LINK_HOME/.codex/AGENTS.md")" == "/tmp/elsewhere.md" ]] \
  || fail "foreign Codex AGENTS.md symlink changed"

guard_command="$(python3 - "$SOURCE/plugins/guardrails/hooks/hooks.json" <<'PY'
import json
import sys
with open(sys.argv[1], encoding="utf-8") as handle:
    print(json.load(handle)["hooks"]["PreToolUse"][0]["hooks"][0]["command"])
PY
)"
set +e
guard_output="$(printf '%s\n' '{"tool_name":"Bash","tool_input":{"command":"git push --force"}}' \
  | bash -c "$guard_command" 2>"$ROOT/hook-blocked.err")"
guard_status=$?
set -e
[[ "$guard_status" -eq 2 ]] || fail "hook guard blocked command exited $guard_status"
[[ "$guard_output" == *'"permissionDecision": "deny"'* ]] || fail "hook guard deny JSON missing"
grep -Fq 'ai-kit guard: git push --force is destructive' "$ROOT/hook-blocked.err" \
  || fail "hook guard stderr reason missing"
allowed_output="$(printf '%s\n' '{"tool_name":"Bash","tool_input":{"command":"git push origin feature/x"}}' \
  | bash -c "$guard_command")"
[[ -z "$allowed_output" ]] || fail "hook guard allowed command wrote stdout"

expect_validator_failure() {
  local label="$1"
  local expected="$2"
  local output
  local status
  set +e
  output="$(python3 "$SOURCE/platforms/ci/validations/check_kit.py" 2>&1)"
  status=$?
  set -e
  [[ "$status" -ne 0 ]] || fail "$label unexpectedly passed validation"
  grep -Fq "$expected" <<<"$output" || fail "$label did not report: $expected"
}

cp "$SOURCE/plugins/guardrails/hooks/hooks.json" "$SOURCE/plugins/guardrails/hooks.json"
expect_validator_failure "root hooks.json" "hooks.json is forbidden"
rm "$SOURCE/plugins/guardrails/hooks.json"

skill="$SOURCE/plugins/guardrails/skills/sdd-spike/SKILL.md"
cp "$skill" "$ROOT/sdd-spike.before"
python3 - "$skill" <<'PY'
from pathlib import Path
import sys
path = Path(sys.argv[1])
path.write_text(path.read_text(encoding="utf-8").replace("disable-model-invocation: true\n", "", 1), encoding="utf-8")
PY
expect_validator_failure "user-only Claude parity" "user-only parity requires"
cp "$ROOT/sdd-spike.before" "$skill"

profile="$SOURCE/plugins/guardrails/agents/researcher.md"
cp "$profile" "$ROOT/researcher.before"
python3 - "$profile" <<'PY'
from pathlib import Path
import sys
path = Path(sys.argv[1])
path.write_text(path.read_text(encoding="utf-8").replace("  - Read\n", "  - Bash\n", 1), encoding="utf-8")
PY
expect_validator_failure "agent tool mapping" "tools must map 1:1"
cp "$ROOT/researcher.before" "$profile"

python3 - "$TEST_HOME/.ai-kit" <<'PY'
import json
from pathlib import Path
import sys

kit = Path(sys.argv[1])
version = (kit / "VERSION").read_text(encoding="utf-8").strip()
repo = "https://github.com/ChristianPrzybulinski/agent-rules-kit.git"
meta = json.loads((kit / ".devin-plugin/plugin.json").read_text(encoding="utf-8"))
assert meta["name"] == "agent-rules-kit"
assert meta["version"] == version
plugin_dirs = sorted(
    path for path in (kit / "plugins").iterdir()
    if (path / ".devin-plugin/plugin.json").is_file()
)
assert [path.name for path in plugin_dirs] == ["guardrails"]  # KIT-047, KIT-055
assert meta["requiredPlugins"] == [
    {"source": "git-subdir", "url": repo, "path": f"plugins/{path.name}"} for path in plugin_dirs
]
assert "optionalPlugins" not in meta
for plugin_dir in plugin_dirs:
    for manifest in (
            plugin_dir / ".devin-plugin/plugin.json",
            plugin_dir / ".claude-plugin/plugin.json",
            plugin_dir / "plugin.json"):
        data = json.loads(manifest.read_text(encoding="utf-8"))
        assert data["version"] == version, manifest
        assert data["name"] == plugin_dir.name, manifest
claude_marketplace = json.loads((kit / ".claude-plugin/marketplace.json").read_text(encoding="utf-8"))
renames = claude_marketplace["renames"]
assert renames["ai-kit"] == "guardrails"
assert renames["core"] == "guardrails"  # KIT-055
assert not set(renames) & {path.name for path in plugin_dirs}
assert {target for target in renames.values() if target} <= {path.name for path in plugin_dirs}
assert claude_marketplace["forceRemoveDeletedPlugins"] is True
listed = {entry["name"]: entry["source"] for entry in claude_marketplace["plugins"]}
assert listed == {path.name: f"./plugins/{path.name}" for path in plugin_dirs}
marketplace = json.loads((kit / ".agents/plugins/marketplace.json").read_text(encoding="utf-8"))
codex_sources = {entry["name"]: entry["source"]["path"] for entry in marketplace["plugins"]}
assert codex_sources == {path.name: f"./plugins/{path.name}" for path in plugin_dirs}
PY

skill_count="$(find "$TEST_HOME/.ai-kit"/plugins/*/skills -mindepth 1 -maxdepth 1 -type d 2>/dev/null | wc -l | tr -d ' ')"
index_count="$(grep -ch "^| \`[a-z0-9-][a-z0-9-]*\` |" "$TEST_HOME/.ai-kit"/plugins/*/INDEX.md | awk '{s+=$1} END {print s+0}')"
[[ "$index_count" == "$skill_count" ]] || fail "$skill_count skills but $index_count index rows"

# sync-project.sh: profile inference plus the generated CLAUDE.md and
# .claude/settings.json (run from the $SOURCE fixture copy, not the live kit).
mkdir -p "$ROOT/proj"
printf '# proj\n' > "$ROOT/proj/AGENTS.md"
touch "$ROOT/proj/project.godot"
if ! "$SOURCE/platforms/tools/sync-project.sh" "$ROOT/proj" >"$ROOT/sync-install.out" 2>&1; then
  cat "$ROOT/sync-install.out" >&2
  fail "sync-project install failed"
fi
grep -Fq 'sync: profile=godot (inferred)' "$ROOT/sync-install.out" \
  || fail "sync-project did not infer the godot profile"
first_hashes="$(shasum -a 256 "$ROOT/proj/CLAUDE.md" "$ROOT/proj/.claude/settings.json")"
if ! "$SOURCE/platforms/tools/sync-project.sh" "$ROOT/proj" >"$ROOT/sync-reinstall.out" 2>&1; then
  cat "$ROOT/sync-reinstall.out" >&2
  fail "second sync-project install failed"
fi
[[ "$(shasum -a 256 "$ROOT/proj/CLAUDE.md" "$ROOT/proj/.claude/settings.json")" == "$first_hashes" ]] \
  || fail "sync-project is not idempotent"
[[ "$(grep -c '@ai-kit' "$ROOT/proj/.claude/settings.json")" == "1" ]] \
  || fail "godot settings.json does not list only guardrails@ai-kit"
if ! "$SOURCE/platforms/tools/sync-project.sh" --check "$ROOT/proj" >"$ROOT/sync-check.out" 2>&1; then
  cat "$ROOT/sync-check.out" >&2
  fail "sync-project --check failed on a generated repo"
fi
python3 - "$ROOT/proj/.claude/settings.json" <<'PY'
import json, sys
path = sys.argv[1]
with open(path, encoding="utf-8") as fh:
    data = json.load(fh)
data["enabledPlugins"]["sdd@ai-kit"] = True
with open(path, "w", encoding="utf-8") as fh:
    fh.write(json.dumps(data, indent=2) + "\n")
PY
set +e
sync_check_out="$("$SOURCE/platforms/tools/sync-project.sh" --check "$ROOT/proj" 2>&1)"
sync_check_status=$?
set -e
[[ "$sync_check_status" -eq 1 ]] || fail "sync-project --check accepted an edited enabledPlugins"
[[ "$sync_check_out" == *"diverges for profile godot"* ]] \
  || fail "sync-project --check did not report the godot divergence"
mkdir -p "$ROOT/proj2"
printf '# mine\n' > "$ROOT/proj2/CLAUDE.md"
touch "$ROOT/proj2/AGENTS.md" "$ROOT/proj2/pom.xml"
set +e
sync_refuse_out="$("$SOURCE/platforms/tools/sync-project.sh" "$ROOT/proj2" 2>&1)"
sync_refuse_status=$?
set -e
[[ "$sync_refuse_status" -eq 1 ]] || fail "sync-project did not refuse a hand-written CLAUDE.md"
[[ "$sync_refuse_out" == *"is not generated"* ]] \
  || fail "sync-project refusal did not report 'is not generated'"
[[ "$(grep -c '^# mine$' "$ROOT/proj2/CLAUDE.md")" == "1" ]] \
  || fail "hand-written CLAUDE.md changed"
[[ ! -e "$ROOT/proj2/.claude/settings.json" ]] || fail "settings.json was written despite the refusal"
[[ ! -e "$ROOT/proj2/.github" ]] || fail ".github was written despite the refusal"

# sync-project.sh also renders the profile's path rules into .claude/rules/
# (restricted PATH like bootstrap/doctor above; still the $SOURCE fixture).
if ! env PATH="$RESTRICTED_PATH" \
    "$SOURCE/platforms/tools/sync-project.sh" --profile godot "$ROOT/proj" \
    >"$ROOT/sync-rules.out" 2>&1; then
  cat "$ROOT/sync-rules.out" >&2
  fail "sync-project rules install failed"
fi
[[ -f "$ROOT/proj/.claude/rules/guardrails-godot.md" ]] \
  || fail "sync-project did not write .claude/rules/guardrails-godot.md"
grep -Fq '<!-- agent-rules-kit: generated from plugins/guardrails/rules/godot.md' \
  "$ROOT/proj/.claude/rules/guardrails-godot.md" || fail "generated rule marker missing"
first_claude_hashes="$(find "$ROOT/proj/.claude" -type f -exec shasum -a 256 {} + | sort)"
if ! env PATH="$RESTRICTED_PATH" \
    "$SOURCE/platforms/tools/sync-project.sh" --profile godot "$ROOT/proj" \
    >"$ROOT/sync-rules-second.out" 2>&1; then
  cat "$ROOT/sync-rules-second.out" >&2
  fail "second sync-project rules install failed"
fi
second_claude_hashes="$(find "$ROOT/proj/.claude" -type f -exec shasum -a 256 {} + | sort)"
[[ "$first_claude_hashes" == "$second_claude_hashes" ]] \
  || fail "sync-project rules install is not idempotent"
if ! env PATH="$RESTRICTED_PATH" \
    "$SOURCE/platforms/tools/sync-project.sh" --check --profile godot "$ROOT/proj" \
    >"$ROOT/sync-rules-check.out" 2>&1; then
  cat "$ROOT/sync-rules-check.out" >&2
  fail "sync-project --check failed on generated .claude/rules"
fi
printf 'x\n' >> "$ROOT/proj/.claude/rules/guardrails-godot.md"
set +e
sync_rules_drift_out="$(env PATH="$RESTRICTED_PATH" \
  "$SOURCE/platforms/tools/sync-project.sh" --check --profile godot "$ROOT/proj" 2>&1)"
sync_rules_drift_status=$?
set -e
[[ "$sync_rules_drift_status" -eq 1 ]] || fail "sync-project --check accepted an edited rule copy"
[[ "$sync_rules_drift_out" == *"diverges from the kit"* ]] \
  || fail "sync-project --check did not report the rule drift"
printf 'mine\n' > "$ROOT/proj/.claude/rules/my-own.md"
if ! env PATH="$RESTRICTED_PATH" \
    "$SOURCE/platforms/tools/sync-project.sh" --profile docs "$ROOT/proj" \
    >"$ROOT/sync-rules-docs.out" 2>&1; then
  cat "$ROOT/sync-rules-docs.out" >&2
  fail "sync-project --profile docs failed"
fi
[[ ! -e "$ROOT/proj/.claude/rules/guardrails-godot.md" ]] \
  || fail "stale generated rule survived the profile switch"
[[ -f "$ROOT/proj/.claude/rules/guardrails-spec.md" ]] \
  || fail "sync-project did not write .claude/rules/guardrails-spec.md"
[[ "$(cat "$ROOT/proj/.claude/rules/my-own.md")" == "mine" ]] \
  || fail "hand-written .claude/rules file was touched"

# KIT-081 stage 2b: the vendored mode is gone; its flag is a usage error that writes nothing.
mkdir -p "$ROOT/vendor-proj"
printf '# proj\n' > "$ROOT/vendor-proj/AGENTS.md"
touch "$ROOT/vendor-proj/project.godot"
set +e
sync_vendor_out="$(env PATH="$RESTRICTED_PATH" \
  "$SOURCE/platforms/tools/sync-project.sh" --vendor-skills "$ROOT/vendor-proj" 2>&1)"
sync_vendor_status=$?
set -e
[[ "$sync_vendor_status" -eq 2 ]] || fail "sync-project accepted --vendor-skills"
[[ "$sync_vendor_out" == *"--vendor-skills was removed in KIT-081 stage 2b"* ]] \
  || fail "sync-project did not say the vendored mode was removed"
[[ ! -e "$ROOT/vendor-proj/.claude" && ! -e "$ROOT/vendor-proj/CLAUDE.md" ]] \
  || fail "sync-project --vendor-skills wrote into the repo"

# sync-project.sh with a comma list (KIT-016): a monorepo with docs at the root,
# Godot under client/ and Java under server/ keeps the union of rules and plugins,
# and a :<dir> profile scopes its rule globs to that folder.
mono_profile="docs,godot:client,java:server"
mkdir -p "$ROOT/mono-proj/docs/spec" "$ROOT/mono-proj/client" "$ROOT/mono-proj/server"
printf '# mono\n' > "$ROOT/mono-proj/AGENTS.md"
touch "$ROOT/mono-proj/client/project.godot" "$ROOT/mono-proj/server/pom.xml"
if ! env PATH="$RESTRICTED_PATH" \
    "$SOURCE/platforms/tools/sync-project.sh" --profile "$mono_profile" "$ROOT/mono-proj" \
    >"$ROOT/sync-mono.out" 2>&1; then
  cat "$ROOT/sync-mono.out" >&2
  fail "multi-profile sync-project install failed"
fi
for r in guardrails-spec guardrails-godot guardrails-java; do
  [[ -f "$ROOT/mono-proj/.claude/rules/$r.md" ]] || fail "multi-profile sync did not write .claude/rules/$r.md"
done
grep -Fqx '  - "client/**/*.gd"' "$ROOT/mono-proj/.claude/rules/guardrails-godot.md" \
  || fail "godot:client did not scope the godot rule to client/"
grep -Fqx '  - "server/**/pom.xml"' "$ROOT/mono-proj/.claude/rules/guardrails-java.md" \
  || fail "java:server did not scope the java rule to server/"
grep -Fqx '  - "docs/spec/**/*.md"' "$ROOT/mono-proj/.claude/rules/guardrails-spec.md" \
  || fail "the unscoped docs profile changed the spec rule globs"
[[ ! -e "$ROOT/mono-proj/.claude/skills" ]] || fail "multi-profile sync copied kit skills into the repo (KIT-081)"
grep -Fq "; profile $mono_profile; AGENTS.md is the source -->" "$ROOT/mono-proj/CLAUDE.md" \
  || fail "CLAUDE.md does not record profile $mono_profile"
first_mono_hashes="$(find "$ROOT/mono-proj/.claude" "$ROOT/mono-proj/CLAUDE.md" -type f -exec shasum -a 256 {} + | sort)"
if ! env PATH="$RESTRICTED_PATH" \
    "$SOURCE/platforms/tools/sync-project.sh" --profile java:server/,docs,godot:client,docs "$ROOT/mono-proj" \
    >"$ROOT/sync-mono-second.out" 2>&1; then
  cat "$ROOT/sync-mono-second.out" >&2
  fail "reordered multi-profile sync-project install failed"
fi
[[ "$(find "$ROOT/mono-proj/.claude" "$ROOT/mono-proj/CLAUDE.md" -type f -exec shasum -a 256 {} + | sort)" == "$first_mono_hashes" ]] \
  || fail "a reordered profile list is not the same sync"
if ! env PATH="$RESTRICTED_PATH" \
    "$SOURCE/platforms/tools/sync-project.sh" --check --profile "$mono_profile" "$ROOT/mono-proj" \
    >"$ROOT/sync-mono-check.out" 2>&1; then
  cat "$ROOT/sync-mono-check.out" >&2
  fail "sync-project --check failed on a multi-profile repo"
fi
set +e
sync_mono_single_out="$(env PATH="$RESTRICTED_PATH" \
  "$SOURCE/platforms/tools/sync-project.sh" --check --profile docs "$ROOT/mono-proj" 2>&1)"
sync_mono_single_status=$?
set -e
[[ "$sync_mono_single_status" -eq 1 ]] || fail "single-profile --check accepted the monorepo's extra rules"
[[ "$sync_mono_single_out" == *"guardrails-godot.md is generated but not in profile"* ]] \
  || fail "single-profile --check did not name the rule it would remove"
set +e
sync_mono_escape_out="$(env PATH="$RESTRICTED_PATH" \
  "$SOURCE/platforms/tools/sync-project.sh" --profile 'docs,godot:../client' "$ROOT/mono-proj" 2>&1)"
sync_mono_escape_status=$?
set -e
[[ "$sync_mono_escape_status" -eq 2 ]] || fail "sync-project accepted a profile folder outside the repo"
[[ "$sync_mono_escape_out" == *"must be a relative path inside the repo"* ]] \
  || fail "sync-project did not explain the rejected profile folder"
[[ "$(find "$ROOT/mono-proj/.claude" "$ROOT/mono-proj/CLAUDE.md" -type f -exec shasum -a 256 {} + | sort)" == "$first_mono_hashes" ]] \
  || fail "a rejected profile list changed the repo"
# Without --profile the list the CLAUDE.md marker records wins over inference (KIT-017, KIT-081 stage 2b),
# so a bare --check passes and a bare write run removes nothing.
if ! env PATH="$RESTRICTED_PATH" \
    "$SOURCE/platforms/tools/sync-project.sh" --check "$ROOT/mono-proj" >"$ROOT/sync-mono-bare-check.out" 2>&1; then
  cat "$ROOT/sync-mono-bare-check.out" >&2
  fail "bare sync-project --check did not keep the CLAUDE.md profile list"
fi
grep -Fqx "sync: profile=$mono_profile (CLAUDE.md)" "$ROOT/sync-mono-bare-check.out" \
  || fail "bare sync-project --check did not report CLAUDE.md as the profile source"
if ! env PATH="$RESTRICTED_PATH" \
    "$SOURCE/platforms/tools/sync-project.sh" "$ROOT/mono-proj" >"$ROOT/sync-mono-bare.out" 2>&1; then
  cat "$ROOT/sync-mono-bare.out" >&2
  fail "bare multi-profile sync-project install failed"
fi
[[ "$(find "$ROOT/mono-proj/.claude" "$ROOT/mono-proj/CLAUDE.md" -type f -exec shasum -a 256 {} + | sort)" == "$first_mono_hashes" ]] \
  || fail "a bare sync dropped the CLAUDE.md profile list"
mkdir -p "$ROOT/mono-plugins-proj"
: > "$ROOT/mono-plugins-proj/AGENTS.md"
if ! env PATH="$RESTRICTED_PATH" \
    "$SOURCE/platforms/tools/sync-project.sh" --profile godot,java "$ROOT/mono-plugins-proj" \
    >"$ROOT/sync-mono-plugins.out" 2>&1; then
  cat "$ROOT/sync-mono-plugins.out" >&2
  fail "multi-profile sync-project install of godot,java failed"
fi
[[ "$(grep -c '@ai-kit' "$ROOT/mono-plugins-proj/.claude/settings.json")" == "1" ]] \
  || fail "godot,java settings.json does not enable only guardrails@ai-kit"

# sync-project.sh writes the spec-tools workflow only into repos with docs/spec (KIT-081 stage 1: the spec tools run
# from the kit): a Java repo without it gets no workflow and --check still passes.
mkdir -p "$ROOT/nospec-proj"
: > "$ROOT/nospec-proj/AGENTS.md"
: > "$ROOT/nospec-proj/pom.xml"
if ! "$SOURCE/platforms/tools/sync-project.sh" "$ROOT/nospec-proj" >"$ROOT/sync-nospec.out" 2>&1; then
  cat "$ROOT/sync-nospec.out" >&2
  fail "sync-project install failed on a repo without docs/spec"
fi
grep -Fq 'sync: no docs/spec, spec tools skipped' "$ROOT/sync-nospec.out" \
  || fail "sync-project did not report the skipped spec tools"
[[ ! -e "$ROOT/nospec-proj/.github" ]] \
  || fail "sync-project wrote .github without docs/spec"
if ! "$SOURCE/platforms/tools/sync-project.sh" --check "$ROOT/nospec-proj" >"$ROOT/sync-nospec-check.out" 2>&1; then
  cat "$ROOT/sync-nospec-check.out" >&2
  fail "sync-project --check failed on a repo without docs/spec"
fi

printf 'smoke: OK (%s skills, app fallback, cleanup, symlink safety, manifests, sync-project, rules copy, no vendored mode, multi-profile sync, no-spec repo)\n' "$skill_count"
