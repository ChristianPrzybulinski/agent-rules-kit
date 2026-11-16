#!/usr/bin/env bash
# Scaffold for the eval case: a protocol folder with one message, plus the kit's `protocol` rule as the synced copy a project carries in
# .claude/rules/, so Claude Code loads it by path when the case reads a matching file (KIT-080, #275). The rule is read
# from this case's plugin folder; a scaffold that cannot reach it stops instead of testing nothing.
set -euo pipefail
rule="$(dirname "${BASH_SOURCE[0]}")/../../rules/protocol.md"
[[ -f "$rule" ]] || { echo "fixture: kit rule $rule not reachable from the scaffold" >&2; exit 1; }
git init -q -b main .
mkdir -p .claude/rules
cp "$rule" .claude/rules/guardrails-protocol.md
mkdir -p protocol
printf '# MoveRequest — command\n\nProtocol version 3. FEAT-012.\n\n| Field | Type | Required |\n|---|---|---|\n| x | int | yes |\n| y | int | yes |\n' > protocol/MoveRequest.md
printf '3\n' > protocol/VERSION
