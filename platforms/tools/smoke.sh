#!/usr/bin/env bash
# Exercises bootstrap and doctor in isolated homes. Usage: smoke.sh
set -euo pipefail

KIT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
ROOT="$(mktemp -d)"
SOURCE="$ROOT/source"
TEST_HOME="$ROOT/home"
RESTRICTED_PATH="/usr/bin:/bin"
export AI_KIT_NO_CODEX_CLI=1

cleanup() {
  rm -rf "$ROOT"
}
trap cleanup EXIT

fail() {
  printf 'FAIL: smoke: %s\n' "$*" >&2
  exit 1
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

replacement = "description: Smoke lifecycle fixture. Use when testing bootstrap and doctor. Not for production guidance (skill testing)."
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

bootstrap_output="$ROOT/bootstrap.out"
if ! env HOME="$TEST_HOME" PATH="$RESTRICTED_PATH" \
    AI_KIT_DIR="$TEST_HOME/.ai-kit" AI_KIT_SOURCE="$SOURCE" AI_KIT_NO_LAUNCHD=1 \
    "$KIT_DIR/platforms/tools/bootstrap.sh" >"$bootstrap_output" 2>&1; then
  cat "$bootstrap_output" >&2
  fail "bootstrap failed"
fi

agents_link="$TEST_HOME/.codex/AGENTS.md"
[[ -L "$agents_link" ]] || fail "Codex AGENTS.md is not a symlink"
resolved="$(python3 -c 'import os,sys; print(os.path.realpath(sys.argv[1]))' "$agents_link")"
expected_resolved="$(python3 -c 'import os,sys; print(os.path.realpath(sys.argv[1]))' "$TEST_HOME/.ai-kit/plugins/core/AGENTS.md")"
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
[[ "$(readlink "$agents_link")" == "$TEST_HOME/.ai-kit/plugins/core/AGENTS.md" ]] \
  || fail "legacy AGENTS.md symlink was not repointed"

rm "$agents_link"
ln -s "$TEST_HOME/.ai-kit/kit/AGENTS.md" "$agents_link"
if ! env HOME="$TEST_HOME" PATH="$RESTRICTED_PATH" AI_KIT_DIR="$TEST_HOME/.ai-kit" \
    "$TEST_HOME/.ai-kit/platforms/tools/doctor.sh" >"$ROOT/doctor-repoint-kit.out" 2>&1; then
  cat "$ROOT/doctor-repoint-kit.out" >&2
  fail "doctor failed to repoint the former kit/ AGENTS.md symlink"
fi
[[ "$(readlink "$agents_link")" == "$TEST_HOME/.ai-kit/plugins/core/AGENTS.md" ]] \
  || fail "former kit/ AGENTS.md symlink was not repointed"

if ! env HOME="$TEST_HOME" PATH="$RESTRICTED_PATH" AI_KIT_DIR="$TEST_HOME/.ai-kit" \
    "$TEST_HOME/.ai-kit/platforms/tools/doctor.sh" >"$ROOT/doctor-initial.out" 2>&1; then
  cat "$ROOT/doctor-initial.out" >&2
  fail "doctor failed after bootstrap"
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
mkdir -p "$APP_HOME/.codex/skills/asset-import"
git clone "$SOURCE" "$APP_HOME/.ai-kit" >/dev/null 2>&1
touch "$APP_HOME/.codex/config.toml"
touch "$APP_HOME/.codex/skills/asset-import/.agent-rules-kit"
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
      echo "core@ai-kit installed, enabled"
    elif [[ -d "$state/plugins" ]]; then
      for installed in "$state/plugins"/*; do
        [[ -f "$installed" ]] && echo "$(basename "$installed")@ai-kit installed, enabled"
      done
    fi
    ;;
  "plugin marketplace add "*)
    touch "$state/marketplace"
    echo "Added marketplace ai-kit"
    ;;
  "plugin add "*@ai-kit)
    mkdir -p "$state/plugins"
    name="${2%@ai-kit}"
    touch "$state/plugins/$name"
    echo "Added plugin $name from marketplace ai-kit."
    ;;
  "plugin marketplace upgrade ai-kit")
    touch "$state/upgrade"
    echo "Upgraded marketplace ai-kit"
    ;;
  "debug prompt-input list skills")
    count="${STUB_EXPOSED:-0}"
    for ((i = 1; i <= count; i++)); do
      echo "core:x$i"
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
  "plugin marketplace add ChristianPrzybulinski/agent-rules-kit --json")
    touch "$state/claude-marketplace"
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
codex_fixes="$(grep -c 'fix: codex plugin .*@ai-kit installed' "$ROOT/doctor-stub-install.out" || true)"
plugin_total="$(find "$STUB_HOME/.ai-kit"/plugins -mindepth 1 -maxdepth 1 -type d | wc -l | tr -d ' ')"
[[ "$codex_fixes" == "$plugin_total" ]] \
  || fail "$codex_fixes codex plugin installs reported, expected $plugin_total"
grep -Fq 'ok: codex plugin exposes 43 kit skills' "$ROOT/doctor-stub-install.out" \
  || fail "stub exposed-skill count was not reported"
grep -Fq 'fix: claude marketplace ai-kit registered' "$ROOT/doctor-stub-install.out" \
  || fail "Claude marketplace add was not reported"
grep -Fq 'fix: claude bundle all@ai-kit installed' "$ROOT/doctor-stub-install.out" \
  || fail "Claude bundle install was not reported"
[[ -f "$STUB_STATE/claude-marketplace" && -f "$STUB_STATE/claude-plugins/all" ]] \
  || fail "Claude stub install markers missing"
[[ "$(readlink "$STUB_HOME/.claude/CLAUDE.md")" == "$STUB_HOME/.ai-kit/plugins/core/AGENTS.md" ]] \
  || fail "Claude CLAUDE.md symlink has the wrong target"
grep -Fq "fix: claude autoCompactWindow set to 200k in $STUB_HOME/.claude/settings.json (KIT-010)" \
  "$ROOT/doctor-stub-install.out" || fail "autoCompactWindow fix was not reported"
[[ "$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["autoCompactWindow"])' \
    "$STUB_HOME/.claude/settings.json")" == "200k" ]] || fail "autoCompactWindow was not written as 200k"
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
grep -Fq 'ok: claude autoCompactWindow 200k' "$ROOT/doctor-stub-no-user-rules.out" \
  || fail "autoCompactWindow 200k was not reported ok on the second run"

# KIT-010: an explicit owner value above the kit's window is kept and reported, never overwritten.
python3 - "$STUB_HOME/.claude/settings.json" <<'PY'
import json
import sys
settings = json.load(open(sys.argv[1]))
settings["autoCompactWindow"] = "500k"
json.dump(settings, open(sys.argv[1], "w"), indent=2)
PY

if ! env HOME="$STUB_HOME" PATH="$stub_path" AI_KIT_NO_CODEX_CLI=0 \
    AI_KIT_DIR="$STUB_HOME/.ai-kit" STUB_STATE_DIR="$STUB_STATE" STUB_EXPOSED=43 \
    AI_KIT_USER_RULES=1 \
    "$STUB_HOME/.ai-kit/platforms/tools/doctor.sh" >"$ROOT/doctor-stub-user-rules.out" 2>&1; then
  cat "$ROOT/doctor-stub-user-rules.out" >&2
  fail "doctor failed to restore user-level rule symlinks"
fi
grep -Fq "warn: claude autoCompactWindow '500k' is above the kit's 200k — kept (owner's choice)" \
  "$ROOT/doctor-stub-user-rules.out" || fail "an owner autoCompactWindow above 200k was not reported"
[[ "$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["autoCompactWindow"])' \
    "$STUB_HOME/.claude/settings.json")" == "500k" ]] || fail "doctor overwrote the owner's autoCompactWindow"
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

if ! env HOME="$STUB_HOME" PATH="$stub_path" AI_KIT_NO_CODEX_CLI=0 \
    AI_KIT_DIR="$STUB_HOME/.ai-kit" STUB_STATE_DIR="$STUB_STATE" STUB_EXPOSED=0 \
    "$STUB_HOME/.ai-kit/platforms/tools/doctor.sh" >"$ROOT/doctor-stub-fallback.out" 2>&1; then
  cat "$ROOT/doctor-stub-fallback.out" >&2
  fail "doctor failed to create stub fallback"
fi
stub_skill_count="$(find "$STUB_HOME/.ai-kit"/plugins/*/skills -mindepth 1 -maxdepth 1 -type d 2>/dev/null | wc -l | tr -d ' ')"
stub_fallback_count="$(find "$STUB_HOME/.codex/skills" -type l | wc -l | tr -d ' ')"
[[ "$stub_fallback_count" == "$stub_skill_count" ]] \
  || fail "$stub_fallback_count stub fallbacks, expected $stub_skill_count"

if ! env HOME="$STUB_HOME" PATH="$stub_path" AI_KIT_NO_CODEX_CLI=0 \
    AI_KIT_DIR="$STUB_HOME/.ai-kit" STUB_STATE_DIR="$STUB_STATE" STUB_EXPOSED=43 \
    "$STUB_HOME/.ai-kit/platforms/tools/doctor.sh" >"$ROOT/doctor-stub-remove.out" 2>&1; then
  cat "$ROOT/doctor-stub-remove.out" >&2
  fail "doctor failed to remove stub fallback"
fi
stub_fallback_count="$(find "$STUB_HOME/.codex/skills" -type l | wc -l | tr -d ' ')"
[[ "$stub_fallback_count" == "0" ]] || fail "stub fallback remained after plugin exposure"
grep -Fq 'ok: codex plugin exposes 43 kit skills' "$ROOT/doctor-stub-remove.out" \
  || fail "stub re-exposure count was not reported"

# KIT-013: a cache that differs from the kit without a version bump is reported, then reinstalled.
printf 'stale\n' >> "$STUB_STATE/claude-cache/all/INDEX.md"
if ! env HOME="$STUB_HOME" PATH="$stub_path" AI_KIT_NO_CODEX_CLI=0 \
    AI_KIT_DIR="$STUB_HOME/.ai-kit" STUB_STATE_DIR="$STUB_STATE" STUB_EXPOSED=43 \
    "$STUB_HOME/.ai-kit/platforms/tools/doctor.sh" >"$ROOT/doctor-stub-stale.out" 2>&1; then
  cat "$ROOT/doctor-stub-stale.out" >&2
  fail "doctor failed with a stale Claude plugin cache"
fi
grep -Fq 'warn: claude plugin all@ai-kit cache differs from the kit — run platforms/tools/refresh.sh' \
  "$ROOT/doctor-stub-stale.out" || fail "doctor did not warn about the stale Claude plugin cache"

if ! env HOME="$STUB_HOME" PATH="$stub_path" AI_KIT_NO_CODEX_CLI=0 \
    AI_KIT_DIR="$STUB_HOME/.ai-kit" STUB_STATE_DIR="$STUB_STATE" \
    "$STUB_HOME/.ai-kit/platforms/tools/refresh.sh" >"$ROOT/refresh-stub.out" 2>&1; then
  cat "$ROOT/refresh-stub.out" >&2
  fail "refresh failed with registered stub marketplace"
fi
[[ -f "$STUB_STATE/upgrade" ]] || fail "refresh did not upgrade the stub marketplace"
[[ -f "$STUB_STATE/claude-marketplace-update" ]] || fail "refresh did not update the Claude marketplace"
[[ -f "$STUB_STATE/claude-plugin-updates/all" ]] || fail "refresh did not update the Claude bundle plugin"
[[ -f "$STUB_STATE/claude-uninstalls/all" && -f "$STUB_STATE/claude-plugins/all" ]] \
  || fail "refresh did not reinstall the stale Claude bundle plugin"
grep -Fq 'refresh: reinstalled Claude plugin all@ai-kit (cache differed from the kit)' "$ROOT/refresh-stub.out" \
  || fail "refresh did not report the Claude reinstall"
diff -rq -x .in_use "$STUB_HOME/.ai-kit/plugins/all" "$STUB_STATE/claude-cache/all" >/dev/null \
  || fail "reinstalled Claude cache still differs from the kit"

rm -rf "$STUB_STATE/claude-uninstalls"
if ! env HOME="$STUB_HOME" PATH="$stub_path" AI_KIT_NO_CODEX_CLI=0 \
    AI_KIT_DIR="$STUB_HOME/.ai-kit" STUB_STATE_DIR="$STUB_STATE" \
    "$STUB_HOME/.ai-kit/platforms/tools/refresh.sh" >"$ROOT/refresh-stub-current.out" 2>&1; then
  cat "$ROOT/refresh-stub-current.out" >&2
  fail "refresh failed with an up-to-date Claude plugin cache"
fi
[[ ! -e "$STUB_STATE/claude-uninstalls" ]] || fail "refresh reinstalled an up-to-date Claude plugin cache"
grep -Fq 'reinstalled' "$ROOT/refresh-stub-current.out" && fail "refresh reported a reinstall of an up-to-date cache"

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

guard_command="$(python3 - "$SOURCE/plugins/core/hooks/hooks.json" <<'PY'
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

cp "$SOURCE/plugins/core/hooks/hooks.json" "$SOURCE/plugins/core/hooks.json"
expect_validator_failure "root hooks.json" "hooks.json is forbidden"
rm "$SOURCE/plugins/core/hooks.json"

skill="$SOURCE/plugins/dev-godot/skills/asset-import/SKILL.md"
cp "$skill" "$ROOT/asset-import.before"
python3 - "$skill" <<'PY'
from pathlib import Path
import sys
path = Path(sys.argv[1])
path.write_text(path.read_text(encoding="utf-8").replace("disable-model-invocation: true\n", "", 1), encoding="utf-8")
PY
expect_validator_failure "user-only Claude parity" "user-only parity requires"
cp "$ROOT/asset-import.before" "$skill"

profile="$SOURCE/plugins/architect-sdd/agents/researcher.md"
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
assert meta["requiredPlugins"] == [{
    "source": "git-subdir",
    "url": repo,
    "path": "plugins/all",
}]
plugin_dirs = sorted(
    path for path in (kit / "plugins").iterdir()
    if (path / ".devin-plugin/plugin.json").is_file()
)
assert len(plugin_dirs) == 14
optional = {entry["path"] for entry in meta["optionalPlugins"]}
assert optional == {f"plugins/{path.name}" for path in plugin_dirs if path.name != "all"}
for plugin_dir in plugin_dirs:
    for manifest in (
            plugin_dir / ".devin-plugin/plugin.json",
            plugin_dir / ".claude-plugin/plugin.json",
            plugin_dir / "plugin.json"):
        data = json.loads(manifest.read_text(encoding="utf-8"))
        assert data["version"] == version, manifest
        assert data["name"] == plugin_dir.name, manifest
claude_marketplace = json.loads((kit / ".claude-plugin/marketplace.json").read_text(encoding="utf-8"))
assert claude_marketplace["renames"] == {"ai-kit": "core"}
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
[[ "$(grep -c '@ai-kit' "$ROOT/proj/.claude/settings.json")" == "5" ]] \
  || fail "godot settings.json does not list exactly 5 @ai-kit plugins"
if ! "$SOURCE/platforms/tools/sync-project.sh" --check "$ROOT/proj" >"$ROOT/sync-check.out" 2>&1; then
  cat "$ROOT/sync-check.out" >&2
  fail "sync-project --check failed on a generated repo"
fi
python3 - "$ROOT/proj/.claude/settings.json" <<'PY'
import json, sys
path = sys.argv[1]
with open(path, encoding="utf-8") as fh:
    data = json.load(fh)
data["enabledPlugins"]["dev-java@ai-kit"] = True
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
[[ ! -e "$ROOT/proj2/.github/spec-lint" ]] || fail "spec-lint was written despite the refusal"

# sync-project.sh also renders the profile's path rules into .claude/rules/
# (restricted PATH like bootstrap/doctor above; still the $SOURCE fixture).
if ! env PATH="$RESTRICTED_PATH" \
    "$SOURCE/platforms/tools/sync-project.sh" --profile godot "$ROOT/proj" \
    >"$ROOT/sync-rules.out" 2>&1; then
  cat "$ROOT/sync-rules.out" >&2
  fail "sync-project rules install failed"
fi
[[ -f "$ROOT/proj/.claude/rules/dev-godot-godot.md" ]] \
  || fail "sync-project did not write .claude/rules/dev-godot-godot.md"
grep -Fq '<!-- agent-rules-kit: generated from plugins/dev-godot/rules/godot.md' \
  "$ROOT/proj/.claude/rules/dev-godot-godot.md" || fail "generated rule marker missing"
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
printf 'x\n' >> "$ROOT/proj/.claude/rules/dev-godot-godot.md"
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
[[ ! -e "$ROOT/proj/.claude/rules/dev-godot-godot.md" ]] \
  || fail "stale generated rule survived the profile switch"
[[ -f "$ROOT/proj/.claude/rules/architect-sdd-spec.md" ]] \
  || fail "sync-project did not write .claude/rules/architect-sdd-spec.md"
[[ "$(cat "$ROOT/proj/.claude/rules/my-own.md")" == "mine" ]] \
  || fail "hand-written .claude/rules file was touched"

# sync-project.sh --vendor-skills: the profile's skill directories are copied
# whole into .claude/skills/ with .agent-rules-kit markers and a hashed
# KIT_MANIFEST.json. Counts come from the $SOURCE fixture at test time (its
# rewritten SKILL.md descriptions differ from the live kit).
godot_plugins="dev-core dev-godot quality-core infra-github" # profile_plugins godot minus core (KIT-002: core loads from the plugin)
expected_skills="$(for p in $godot_plugins; do ls "$SOURCE/plugins/$p/skills"; done | wc -l | tr -d ' ')"
expected_files=$(( $(for p in $godot_plugins; do find "$SOURCE/plugins/$p/skills" -type f; done | wc -l) + expected_skills ))
mkdir -p "$ROOT/vendor-proj/.claude/skills/review-loop"
printf '# proj\n' > "$ROOT/vendor-proj/AGENTS.md"
touch "$ROOT/vendor-proj/project.godot"
printf 'mine\n' > "$ROOT/vendor-proj/.claude/skills/review-loop/SKILL.md"
if ! env PATH="$RESTRICTED_PATH" \
    "$SOURCE/platforms/tools/sync-project.sh" --vendor-skills "$ROOT/vendor-proj" \
    >"$ROOT/sync-vendor.out" 2>&1; then
  cat "$ROOT/sync-vendor.out" >&2
  fail "sync-project --vendor-skills install failed"
fi
grep -Fq 'sync: skills=vendored' "$ROOT/sync-vendor.out" \
  || fail "sync-project did not report the vendored mode"
[[ "$(find "$ROOT/vendor-proj/.claude/skills" -name .agent-rules-kit | wc -l | tr -d ' ')" == "$expected_skills" ]] \
  || fail "vendored marker count differs from $expected_skills"
manifest_files="$(python3 -c 'import json,sys; print(sum(len(s["files"]) for s in json.load(open(sys.argv[1]))["skills"].values()))' \
  "$ROOT/vendor-proj/.claude/skills/KIT_MANIFEST.json")"
[[ "$manifest_files" == "$expected_files" ]] \
  || fail "manifest lists $manifest_files files, expected $expected_files"
for p in $godot_plugins; do
  for s in "$SOURCE/plugins/$p/skills"/*/; do
    [[ -f "$s/SKILL.md" ]] || continue
    n="${s%/}"
    n="${n##*/}"
    vendor_diff="$(diff -r -q "$s" "$ROOT/vendor-proj/.claude/skills/$n" || true)"
    [[ "$vendor_diff" == "Only in $ROOT/vendor-proj/.claude/skills/$n: .agent-rules-kit" ]] \
      || fail "vendored $n differs from the kit copy: $vendor_diff"
  done
done
[[ "$(cat "$ROOT/vendor-proj/.claude/skills/review-loop/SKILL.md")" == "mine" ]] \
  || fail "hand-written review-loop skill was touched"
[[ "$(grep -c '@ai-kit' "$ROOT/vendor-proj/.claude/settings.json")" == "1" ]] \
  || fail "vendored settings.json does not keep exactly core@ai-kit"
first_vendor_hashes="$(find "$ROOT/vendor-proj/.claude" -type f -exec shasum -a 256 {} + | sort)"
if ! env PATH="$RESTRICTED_PATH" \
    "$SOURCE/platforms/tools/sync-project.sh" "$ROOT/vendor-proj" \
    >"$ROOT/sync-vendor-second.out" 2>&1; then
  cat "$ROOT/sync-vendor-second.out" >&2
  fail "second vendored sync-project install failed"
fi
grep -Fq 'sync: skills=vendored' "$ROOT/sync-vendor-second.out" \
  || fail "the manifest did not keep the vendored mode"
second_vendor_hashes="$(find "$ROOT/vendor-proj/.claude" -type f -exec shasum -a 256 {} + | sort)"
[[ "$first_vendor_hashes" == "$second_vendor_hashes" ]] \
  || fail "vendored sync-project is not idempotent"
if ! env PATH="$RESTRICTED_PATH" \
    "$SOURCE/platforms/tools/sync-project.sh" --check "$ROOT/vendor-proj" \
    >"$ROOT/sync-vendor-check.out" 2>&1; then
  cat "$ROOT/sync-vendor-check.out" >&2
  fail "sync-project --check failed on a vendored repo"
fi
printf x >> "$ROOT/vendor-proj/.claude/skills/godot-standards/SKILL.md"
set +e
sync_vendor_drift_out="$(env PATH="$RESTRICTED_PATH" \
  "$SOURCE/platforms/tools/sync-project.sh" --check "$ROOT/vendor-proj" 2>&1)"
sync_vendor_drift_status=$?
set -e
[[ "$sync_vendor_drift_status" -eq 1 ]] \
  || fail "sync-project --check accepted an edited vendored skill"
[[ "$sync_vendor_drift_out" == *"diverges from the manifest"* ]] \
  || fail "sync-project --check did not report the skill drift"
if ! env PATH="$RESTRICTED_PATH" \
    "$SOURCE/platforms/tools/sync-project.sh" "$ROOT/vendor-proj" \
    >"$ROOT/sync-vendor-resync.out" 2>&1; then
  cat "$ROOT/sync-vendor-resync.out" >&2
  fail "vendored resync after the edit failed"
fi
printf 'extra\n' > "$ROOT/vendor-proj/.claude/skills/github-cli/extra.txt"
set +e
sync_vendor_extra_out="$(env PATH="$RESTRICTED_PATH" \
  "$SOURCE/platforms/tools/sync-project.sh" --check "$ROOT/vendor-proj" 2>&1)"
sync_vendor_extra_status=$?
set -e
[[ "$sync_vendor_extra_status" -eq 1 ]] \
  || fail "sync-project --check accepted an extra vendored file"
[[ "$sync_vendor_extra_out" == *"not in manifest"* ]] \
  || fail "sync-project --check did not report the extra file"
if ! env PATH="$RESTRICTED_PATH" \
    "$SOURCE/platforms/tools/sync-project.sh" --profile docs "$ROOT/vendor-proj" \
    >"$ROOT/sync-vendor-docs.out" 2>&1; then
  cat "$ROOT/sync-vendor-docs.out" >&2
  fail "vendored sync-project --profile docs failed"
fi
[[ ! -e "$ROOT/vendor-proj/.claude/skills/godot-standards" ]] \
  || fail "godot-standards survived the profile switch"
[[ -f "$ROOT/vendor-proj/.claude/skills/sdd-tasks/SKILL.md" ]] \
  || fail "sdd-tasks missing after the profile switch"
[[ "$(cat "$ROOT/vendor-proj/.claude/skills/review-loop/SKILL.md")" == "mine" ]] \
  || fail "hand-written review-loop skill was touched by the profile switch"
[[ ! -e "$ROOT/vendor-proj/.claude/skills/github-cli/extra.txt" ]] \
  || fail "extra file survived the github-cli regeneration"
mkdir -p "$ROOT/vendor-proj2/.claude/skills/github-cli"
printf '# mine\n' > "$ROOT/vendor-proj2/AGENTS.md"
touch "$ROOT/vendor-proj2/project.godot"
set +e
sync_vendor_refuse_out="$(env PATH="$RESTRICTED_PATH" \
  "$SOURCE/platforms/tools/sync-project.sh" --vendor-skills "$ROOT/vendor-proj2" 2>&1)"
sync_vendor_refuse_status=$?
set -e
[[ "$sync_vendor_refuse_status" -eq 1 ]] \
  || fail "sync-project did not refuse an unmarked .claude/skills/github-cli"
[[ "$sync_vendor_refuse_out" == *"is not generated"* ]] \
  || fail "sync-project refusal did not report 'is not generated'"
[[ ! -e "$ROOT/vendor-proj2/.claude/skills/KIT_MANIFEST.json" ]] \
  || fail "manifest was written despite the refusal"
[[ ! -e "$ROOT/vendor-proj2/.claude/settings.json" ]] \
  || fail "settings.json was written despite the refusal"

# sync-project.sh with a comma list (KIT-016): a monorepo with docs at the root,
# Godot under client/ and Java under server/ keeps the union of rules, plugins and
# vendored skills, and a :<dir> profile scopes its rule globs to that folder.
mono_profile="docs,godot:client,java:server"
mkdir -p "$ROOT/mono-proj/docs/spec" "$ROOT/mono-proj/client" "$ROOT/mono-proj/server"
printf '# mono\n' > "$ROOT/mono-proj/AGENTS.md"
touch "$ROOT/mono-proj/client/project.godot" "$ROOT/mono-proj/server/pom.xml"
if ! env PATH="$RESTRICTED_PATH" \
    "$SOURCE/platforms/tools/sync-project.sh" --profile "$mono_profile" --vendor-skills "$ROOT/mono-proj" \
    >"$ROOT/sync-mono.out" 2>&1; then
  cat "$ROOT/sync-mono.out" >&2
  fail "multi-profile sync-project install failed"
fi
for r in architect-sdd-spec dev-godot-godot dev-java-java; do
  [[ -f "$ROOT/mono-proj/.claude/rules/$r.md" ]] || fail "multi-profile sync did not write .claude/rules/$r.md"
done
grep -Fqx '  - "client/**/*.gd"' "$ROOT/mono-proj/.claude/rules/dev-godot-godot.md" \
  || fail "godot:client did not scope the godot rule to client/"
grep -Fqx '  - "server/**/pom.xml"' "$ROOT/mono-proj/.claude/rules/dev-java-java.md" \
  || fail "java:server did not scope the java rule to server/"
grep -Fqx '  - "docs/spec/**/*.md"' "$ROOT/mono-proj/.claude/rules/architect-sdd-spec.md" \
  || fail "the unscoped docs profile changed the spec rule globs"
for s in sdd-tasks godot-standards java-standards postgresql; do
  [[ -f "$ROOT/mono-proj/.claude/skills/$s/.agent-rules-kit" ]] || fail "multi-profile sync did not vendor $s"
done
[[ "$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["profile"])' \
    "$ROOT/mono-proj/.claude/skills/KIT_MANIFEST.json")" == "$mono_profile" ]] \
  || fail "manifest does not record profile $mono_profile"
first_mono_hashes="$(find "$ROOT/mono-proj/.claude" -type f -exec shasum -a 256 {} + | sort)"
if ! env PATH="$RESTRICTED_PATH" \
    "$SOURCE/platforms/tools/sync-project.sh" --profile java:server/,docs,godot:client,docs "$ROOT/mono-proj" \
    >"$ROOT/sync-mono-second.out" 2>&1; then
  cat "$ROOT/sync-mono-second.out" >&2
  fail "reordered multi-profile sync-project install failed"
fi
[[ "$(find "$ROOT/mono-proj/.claude" -type f -exec shasum -a 256 {} + | sort)" == "$first_mono_hashes" ]] \
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
[[ "$sync_mono_single_out" == *"dev-godot-godot.md is generated but not in profile"* ]] \
  || fail "single-profile --check did not name the rule it would remove"
set +e
sync_mono_escape_out="$(env PATH="$RESTRICTED_PATH" \
  "$SOURCE/platforms/tools/sync-project.sh" --profile 'docs,godot:../client' "$ROOT/mono-proj" 2>&1)"
sync_mono_escape_status=$?
set -e
[[ "$sync_mono_escape_status" -eq 2 ]] || fail "sync-project accepted a profile folder outside the repo"
[[ "$sync_mono_escape_out" == *"must be a relative path inside the repo"* ]] \
  || fail "sync-project did not explain the rejected profile folder"
[[ "$(find "$ROOT/mono-proj/.claude" -type f -exec shasum -a 256 {} + | sort)" == "$first_mono_hashes" ]] \
  || fail "a rejected profile list changed the repo"
# Without --profile the list KIT_MANIFEST.json records wins over inference (KIT-017),
# so a bare --check passes and a bare write run removes nothing.
if ! env PATH="$RESTRICTED_PATH" \
    "$SOURCE/platforms/tools/sync-project.sh" --check "$ROOT/mono-proj" >"$ROOT/sync-mono-bare-check.out" 2>&1; then
  cat "$ROOT/sync-mono-bare-check.out" >&2
  fail "bare sync-project --check did not keep the manifest's profile list"
fi
grep -Fqx "sync: profile=$mono_profile (manifest)" "$ROOT/sync-mono-bare-check.out" \
  || fail "bare sync-project --check did not report the manifest as the profile source"
if ! env PATH="$RESTRICTED_PATH" \
    "$SOURCE/platforms/tools/sync-project.sh" "$ROOT/mono-proj" >"$ROOT/sync-mono-bare.out" 2>&1; then
  cat "$ROOT/sync-mono-bare.out" >&2
  fail "bare multi-profile sync-project install failed"
fi
[[ "$(find "$ROOT/mono-proj/.claude" -type f -exec shasum -a 256 {} + | sort)" == "$first_mono_hashes" ]] \
  || fail "a bare sync dropped the manifest's profile list"
mkdir -p "$ROOT/mono-plugins-proj"
: > "$ROOT/mono-plugins-proj/AGENTS.md"
if ! env PATH="$RESTRICTED_PATH" \
    "$SOURCE/platforms/tools/sync-project.sh" --profile godot,java "$ROOT/mono-plugins-proj" \
    >"$ROOT/sync-mono-plugins.out" 2>&1; then
  cat "$ROOT/sync-mono-plugins.out" >&2
  fail "multi-profile sync-project install without vendoring failed"
fi
[[ "$(grep -c '@ai-kit' "$ROOT/mono-plugins-proj/.claude/settings.json")" == "9" ]] \
  || fail "godot,java settings.json does not enable the 9-plugin union"

# sync-project.sh copies the spec validator only into repos with docs/spec: a
# Java repo without it gets no .github/spec-lint and --check still passes.
mkdir -p "$ROOT/nospec-proj"
: > "$ROOT/nospec-proj/AGENTS.md"
: > "$ROOT/nospec-proj/pom.xml"
if ! "$SOURCE/platforms/tools/sync-project.sh" "$ROOT/nospec-proj" >"$ROOT/sync-nospec.out" 2>&1; then
  cat "$ROOT/sync-nospec.out" >&2
  fail "sync-project install failed on a repo without docs/spec"
fi
grep -Fq 'sync: no docs/spec, spec-lint skipped' "$ROOT/sync-nospec.out" \
  || fail "sync-project did not report the skipped spec-lint"
[[ ! -e "$ROOT/nospec-proj/.github/spec-lint" ]] \
  || fail "sync-project wrote .github/spec-lint without docs/spec"
if ! "$SOURCE/platforms/tools/sync-project.sh" --check "$ROOT/nospec-proj" >"$ROOT/sync-nospec-check.out" 2>&1; then
  cat "$ROOT/sync-nospec-check.out" >&2
  fail "sync-project --check failed on a repo without docs/spec"
fi

printf 'smoke: OK (%s skills, app fallback, cleanup, symlink safety, manifests, sync-project, rules copy, vendored skills, multi-profile sync, no-spec repo)\n' "$skill_count"
