#!/usr/bin/env bash
# Install smoke test in a throwaway HOME. Usage: install-smoke.sh
# Runs all.sh twice (idempotent), plants unmarked user skills, runs --clean and
# asserts they survive, every kit skill carries its marker and the always-on
# files match agents/AGENTS.md. Never touches the real HOME.
set -euo pipefail

KIT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
unset CODEX_HOME
export HOME
HOME="$(mktemp -d)"
trap 'rm -rf "${HOME:?}"' EXIT

fail() { echo "FAIL: install-smoke: $*" >&2; exit 1; }

"$KIT_DIR/platforms/install/all.sh" >/dev/null
"$KIT_DIR/platforms/install/all.sh" >/dev/null

mkdir -p "$HOME/.agents/skills/my-own" "$HOME/.config/devin/skills/personal"
touch "$HOME/.agents/skills/my-own/SKILL.md" "$HOME/.config/devin/skills/personal/SKILL.md"
"$KIT_DIR/platforms/install/all.sh" --clean >/dev/null

[[ -f "$HOME/.agents/skills/my-own/SKILL.md" ]] || fail "--clean removed an unmarked user skill in ~/.agents/skills"
[[ -f "$HOME/.config/devin/skills/personal/SKILL.md" ]] || fail "--clean removed user content in ~/.config/devin/skills"

expected="$(find "$KIT_DIR/agents/skills" -name SKILL.md | wc -l | tr -d ' ')"
for dest in "$HOME/.agents/skills" "$HOME/.codeium/windsurf/skills"; do
  got="$(find "$dest" -mindepth 2 -maxdepth 2 -name .agent-rules-kit | wc -l | tr -d ' ')"
  [[ "$got" == "$expected" ]] || fail "$dest: $got marked skills, expected $expected"
done
for f in .config/devin/AGENTS.md .codeium/windsurf/memories/global_rules.md .codex/AGENTS.md; do
  cmp -s "$KIT_DIR/agents/AGENTS.md" "$HOME/$f" || fail "$f differs from agents/AGENTS.md"
done
[[ "$(cat "$HOME/.config/agent-rules-kit/VERSION")" == "$(cat "$KIT_DIR/VERSION")" ]] || fail "installed VERSION differs from the repo"

echo "install-smoke: OK ($expected skills installed, --clean keeps user content)"
