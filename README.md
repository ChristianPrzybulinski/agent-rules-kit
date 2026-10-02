# agent-rules-kit

A plugin-first source of always-on rules, triggered rules, skills, references and templates for Devin Cloud, Devin CLI/Desktop and Codex.

**Layout:** [`INDEX.md`](INDEX.md) · **Maintenance:** [`docs/maintenance.md`](docs/maintenance.md)

## Bootstrap

Private repository access requires `gh auth login`; run `gh auth setup-git` once so plain Git reuses those credentials.

```bash
gh repo clone ChristianPrzybulinski/agent-rules-kit ~/.ai-kit && ~/.ai-kit/platforms/tools/bootstrap.sh
```

## How each agent loads the kit

| Agent | Always-on | Skills | Triggered rules | Templates/references | Refresh |
|---|---|---|---|---|---|
| Devin Cloud | plugin `AGENTS.md` | plugin `skills/` | plugin `rules/` | in the plugin | fetches `main` per session |
| Devin CLI/Desktop | plugin | plugin | plugin | in the plugin | app startup; doctor updates stale plugin SHA |
| Codex | `~/.codex/AGENTS.md` symlink | marketplace plugin `ai-kit@ai-kit` plus temporary fallback symlinks | n/a (skill descriptions trigger) | relative paths in the clone | launchd every six hours |

## Devin plugin

Install `ChristianPrzybulinski/agent-rules-kit` at `ref: main` in personal or managed scope. To migrate an existing `ref: devin-plugin` manifest: Customize → Plugins → Plugin settings → Edit manifest, change the ref to `main`, then Reindex. Run `devin plugins update ai-kit` to force a refresh.

## Codex

Bootstrap links `~/.codex/AGENTS.md` to `~/.ai-kit/AGENTS.md` and registers the marketplace:

```bash
codex plugin marketplace add ChristianPrzybulinski/agent-rules-kit --ref main
codex plugin add ai-kit@ai-kit
```

While [openai/codex#22078](https://github.com/openai/codex/issues/22078) remains open, installed plugin skills may not be exposed to the model. `doctor.sh` therefore maintains `~/.codex/skills/<name>` symlinks and removes them automatically once `codex debug prompt-input` exposes `ai-kit:*` skills. When only the desktop app is discoverable, doctor uses app-only mode and keeps the fallback active.

## Refresh and diagnosis

On macOS, launchd runs `platforms/tools/refresh.sh` at login and every six hours. `platforms/tools/doctor.sh` diagnoses and safely repairs clone, plugin, symlink and legacy state. Nothing refreshes at agent session start.
