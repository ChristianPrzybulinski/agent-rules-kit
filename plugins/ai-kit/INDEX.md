# plugins/ai-kit/ — plugin root

Scope: content shared by Devin, Codex and Claude Code. Repository tooling and documentation stay outside this directory.

| Entry | Purpose | When loaded |
|---|---|---|
| [`AGENTS.md`](AGENTS.md) | global always-on rules | every plugin session |
| [`rules/`](rules/) ([java](rules/java.md), [Godot](rules/godot.md), [spec](rules/spec.md)) | Devin triggered rules | matching glob or explicit trigger |
| [`agents/`](agents/) | shared Devin/Claude subagent profiles | local Devin and Claude Code |
| [`hooks/hooks.json`](hooks/hooks.json) | shared best-effort PreToolUse command guard | local Devin and Claude Code |
| [`skills/`](skills/INDEX.md) | flat invocable procedures and references | model or user invocation |
| [`templates/`](templates/INDEX.md) | governed artifact skeletons | when a skill creates an artifact |
| [`.devin-plugin/plugin.json`](.devin-plugin/plugin.json) | Devin plugin manifest | Devin discovery/install |
| [`.claude-plugin/plugin.json`](.claude-plugin/plugin.json) | Claude Code plugin manifest | Claude discovery/install |
| [`plugin.json`](plugin.json) | portable Codex plugin manifest | Codex marketplace discovery |
