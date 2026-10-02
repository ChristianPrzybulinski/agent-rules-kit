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
for skill in Path(sys.argv[1], "kit", "skills").glob("*/SKILL.md"):
    lines = skill.read_text(encoding="utf-8").splitlines()
    for index, line in enumerate(lines):
        if line.startswith("description: "):
            lines[index] = replacement
            break
    skill.write_text("\n".join(lines) + "\n", encoding="utf-8")
PY

git -C "$SOURCE" init -q -b main
git -C "$SOURCE" add -A
git -C "$SOURCE" -c user.name=smoke -c user.email=smoke@example.invalid commit -q -m "test fixture"

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
expected_resolved="$(python3 -c 'import os,sys; print(os.path.realpath(sys.argv[1]))' "$TEST_HOME/.ai-kit/kit/AGENTS.md")"
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
[[ "$(readlink "$agents_link")" == "$TEST_HOME/.ai-kit/kit/AGENTS.md" ]] \
  || fail "legacy AGENTS.md symlink was not repointed"

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
app_skill_count="$(find "$APP_HOME/.ai-kit/kit/skills" -mindepth 1 -maxdepth 1 -type d | wc -l | tr -d ' ')"
fallback_count=0
for skill_file in "$APP_HOME/.ai-kit"/kit/skills/*/SKILL.md; do
  [[ -f "$skill_file" ]] || continue
  name="$(basename "$(dirname "$skill_file")")"
  fallback="$APP_HOME/.codex/skills/$name"
  expected="$APP_HOME/.ai-kit/kit/skills/$name"
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
    if [[ "${STUB_PLUGIN:-0}" == "1" || -f "$state/plugin" ]]; then
      echo "ai-kit@ai-kit installed, enabled"
    fi
    ;;
  "plugin marketplace add "*)
    touch "$state/marketplace"
    echo "Added marketplace ai-kit"
    ;;
  "plugin add ai-kit@ai-kit")
    touch "$state/plugin"
    echo "Added plugin ai-kit from marketplace ai-kit."
    ;;
  "plugin marketplace upgrade ai-kit")
    touch "$state/upgrade"
    echo "Upgraded marketplace ai-kit"
    ;;
  "debug prompt-input list skills")
    count="${STUB_EXPOSED:-0}"
    for ((i = 1; i <= count; i++)); do
      echo "ai-kit:x$i"
    done
    ;;
  *)
    echo "unexpected codex stub arguments: $*" >&2
    exit 2
    ;;
esac
STUB
chmod +x "$STUB_BIN/codex"
git clone "$SOURCE" "$STUB_HOME/.ai-kit" >/dev/null 2>&1

stub_path="$STUB_BIN:$RESTRICTED_PATH"
if ! env HOME="$STUB_HOME" PATH="$stub_path" AI_KIT_NO_CODEX_CLI=0 \
    AI_KIT_DIR="$STUB_HOME/.ai-kit" STUB_STATE_DIR="$STUB_STATE" STUB_EXPOSED=43 \
    "$STUB_HOME/.ai-kit/platforms/tools/doctor.sh" >"$ROOT/doctor-stub-install.out" 2>&1; then
  cat "$ROOT/doctor-stub-install.out" >&2
  fail "doctor failed to install stub marketplace/plugin"
fi
grep -Fq 'fix: codex marketplace ai-kit registered' "$ROOT/doctor-stub-install.out" \
  || fail "stub marketplace add was not reported"
grep -Fq 'fix: codex plugin ai-kit@ai-kit installed' "$ROOT/doctor-stub-install.out" \
  || fail "stub plugin add was not reported"
grep -Fq 'ok: codex plugin exposes 43 ai-kit skills' "$ROOT/doctor-stub-install.out" \
  || fail "stub exposed-skill count was not reported"
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
stub_skill_count="$(find "$STUB_HOME/.ai-kit/kit/skills" -mindepth 1 -maxdepth 1 -type d | wc -l | tr -d ' ')"
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
grep -Fq 'ok: codex plugin exposes 43 ai-kit skills' "$ROOT/doctor-stub-remove.out" \
  || fail "stub re-exposure count was not reported"

if ! env HOME="$STUB_HOME" PATH="$stub_path" AI_KIT_NO_CODEX_CLI=0 \
    AI_KIT_DIR="$STUB_HOME/.ai-kit" STUB_STATE_DIR="$STUB_STATE" \
    "$STUB_HOME/.ai-kit/platforms/tools/refresh.sh" >"$ROOT/refresh-stub.out" 2>&1; then
  cat "$ROOT/refresh-stub.out" >&2
  fail "refresh failed with registered stub marketplace"
fi
[[ -f "$STUB_STATE/upgrade" ]] || fail "refresh did not upgrade the stub marketplace"

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

python3 - "$TEST_HOME/.ai-kit" <<'PY'
import json
from pathlib import Path
import sys

kit = Path(sys.argv[1])
version = (kit / "VERSION").read_text(encoding="utf-8").strip()
for manifest in (kit / "kit/.devin-plugin/plugin.json", kit / "kit/plugin.json"):
    assert json.loads(manifest.read_text(encoding="utf-8"))["version"] == version
marketplace = json.loads((kit / ".agents/plugins/marketplace.json").read_text(encoding="utf-8"))
assert marketplace["plugins"][0]["source"]["path"] == "./kit"
PY

skill_count="$(find "$TEST_HOME/.ai-kit/kit/skills" -mindepth 1 -maxdepth 1 -type d | wc -l | tr -d ' ')"
index_count="$(grep -c "^| \`[a-z0-9-][a-z0-9-]*\` |" "$TEST_HOME/.ai-kit/kit/skills/INDEX.md")"
[[ "$skill_count" == "$index_count" ]] || fail "$skill_count skill folders but $index_count index rows"

printf 'smoke: OK (%s skills, app fallback, cleanup, symlink safety, manifests)\n' "$skill_count"
