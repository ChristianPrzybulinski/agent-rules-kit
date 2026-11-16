#!/usr/bin/env bash
# Scaffold for the eval case: a Godot 4 project, plus the kit's `godot` rule as the synced copy a project carries in
# .claude/rules/, so Claude Code loads it by path when the case reads a matching file (KIT-080, #275). The rule is read
# from this case's plugin folder; a scaffold that cannot reach it stops instead of testing nothing.
set -euo pipefail
rule="$(dirname "${BASH_SOURCE[0]}")/../../rules/godot.md"
[[ -f "$rule" ]] || { echo "fixture: kit rule $rule not reachable from the scaffold" >&2; exit 1; }
git init -q -b main .
mkdir -p .claude/rules
cp "$rule" .claude/rules/guardrails-godot.md
printf '; Engine configuration file.\nconfig_version=5\n\n[application]\nconfig/name="Boot"\nrun/main_scene="res://main.tscn"\n' > project.godot
printf 'extends Node\n\nfunc _ready() -> void:\n\tprint("ready")\n' > main.gd
