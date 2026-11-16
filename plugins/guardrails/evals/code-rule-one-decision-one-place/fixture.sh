#!/usr/bin/env bash
# Scaffold for the eval case: two GDScript files that copy one threshold, plus the kit's `code` rule as the synced copy a project carries in
# .claude/rules/, so Claude Code loads it by path when the case reads a matching file (KIT-080, #275). The rule is read
# from this case's plugin folder; a scaffold that cannot reach it stops instead of testing nothing.
set -euo pipefail
rule="$(dirname "${BASH_SOURCE[0]}")/../../rules/code.md"
[[ -f "$rule" ]] || { echo "fixture: kit rule $rule not reachable from the scaffold" >&2; exit 1; }
git init -q -b main .
mkdir -p .claude/rules
cp "$rule" .claude/rules/guardrails-code.md
mkdir -p features/party app/network
printf 'extends Node\n\nfunc can_show_evolve_button(level: int) -> bool:\n\treturn level >= 30\n' > features/party/party_panel.gd
printf 'extends RefCounted\n\nfunc is_valid_evolve(level: int) -> bool:\n\tif level < 30:\n\t\treturn false\n\treturn true\n' > app/network/evolve_request.gd
