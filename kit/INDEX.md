# kit/ — ai-kit plugin root

Scope: content loaded by Devin and Codex. Repository tooling and documentation stay outside this directory.

| Entry | Purpose | When loaded |
|---|---|---|
| [`AGENTS.md`](AGENTS.md) | global always-on rules | every plugin session |
| [`rules/`](rules/) ([java](rules/java.md), [Godot](rules/godot.md), [spec](rules/spec.md)) | Devin triggered rules | matching glob or explicit trigger |
| [`skills/`](skills/INDEX.md) | flat invocable procedures and references | model or user invocation |
| [`templates/`](templates/INDEX.md) | governed artifact skeletons | when a skill creates an artifact |
| [`.devin-plugin/plugin.json`](.devin-plugin/plugin.json) | Devin plugin manifest | plugin discovery/install |
| [`plugin.json`](plugin.json) | portable Codex plugin manifest | marketplace plugin discovery |
