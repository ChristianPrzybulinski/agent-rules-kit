# agent-rules-kit

A plugin-first source of always-on rules, triggered rules, skills, references and templates for Devin Cloud, Devin CLI/Desktop and Codex. Plugin content lives under [`plugins/ai-kit/`](plugins/ai-kit/INDEX.md); tooling and documentation stay at repository root.

**Repository layout:** [`INDEX.md`](INDEX.md) · **Maintenance:** [`docs/maintenance.md`](docs/maintenance.md)

## Bootstrap

Private repository access requires `gh auth login`; run `gh auth setup-git` once so plain Git reuses those credentials.

```bash
gh repo clone ChristianPrzybulinski/agent-rules-kit ~/.ai-kit && ~/.ai-kit/platforms/tools/bootstrap.sh
```

## How each agent loads the kit

| Agent | Always-on | Skills/rules | Refresh |
|---|---|---|---|
| Devin Cloud | required plugin `plugins/ai-kit/AGENTS.md` | `plugins/ai-kit/skills/` and `plugins/ai-kit/rules/` | fetches `main` per session |
| Devin CLI/Desktop | root meta-plugin requires `plugins/ai-kit/` | required plugin contents | app startup; doctor updates stale SHA |
| Codex | `~/.codex/AGENTS.md` → `~/.ai-kit/plugins/ai-kit/AGENTS.md` | marketplace plugin plus temporary fallback symlinks | launchd every six hours |

## Devin plugin

The existing repository source remains valid because its content-free root meta-plugin requires the real plugin from `plugins/ai-kit/`:

```bash
devin plugins install ChristianPrzybulinski/agent-rules-kit
```

The direct alternative is `devin plugins install ChristianPrzybulinski/agent-rules-kit#plugins/ai-kit`. Existing Customize entries need no source change; Reindex to pick up the new dependency. Run `devin plugins update ai-kit` to force a local refresh.

## Codex

Bootstrap registers the marketplace and plugin:

```bash
codex plugin marketplace add ChristianPrzybulinski/agent-rules-kit --ref main
codex plugin add ai-kit@ai-kit
```

The root marketplace catalog points to `./plugins/ai-kit`; `~/.codex/AGENTS.md` links to `~/.ai-kit/plugins/ai-kit/AGENTS.md`. While [openai/codex#22078](https://github.com/openai/codex/issues/22078) remains open, doctor maintains fallback skill symlinks to `~/.ai-kit/plugins/ai-kit/skills/` and removes them once `ai-kit:*` skills are exposed.

## Refresh and diagnosis

On macOS, launchd runs `platforms/tools/refresh.sh` at login and every six hours. `platforms/tools/doctor.sh` repairs clone, plugin and symlink state. Nothing refreshes at agent session start.

## Maintainers

The plugin root is `plugins/ai-kit/`; the repository root is a content-free meta-plugin. Before a PR, run `platforms/tools/check.sh` and `platforms/tools/smoke.sh`. Content changes follow `docs/maintenance.md`. Never add non-rule files to `plugins/ai-kit/rules/`, and never create `agents/` at a plugin root.
