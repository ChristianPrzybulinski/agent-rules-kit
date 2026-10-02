# agent-rules-kit

A plugin-first source of always-on rules, triggered rules, skills, references and templates for Devin Cloud, Devin CLI/Desktop and Codex. Plugin content lives under [`kit/`](kit/INDEX.md); tooling and documentation stay at repository root.

**Repository layout:** [`INDEX.md`](INDEX.md) · **Maintenance:** [`docs/maintenance.md`](docs/maintenance.md)

## Bootstrap

Private repository access requires `gh auth login`; run `gh auth setup-git` once so plain Git reuses those credentials.

```bash
gh repo clone ChristianPrzybulinski/agent-rules-kit ~/.ai-kit && ~/.ai-kit/platforms/tools/bootstrap.sh
```

## How each agent loads the kit

| Agent | Always-on | Skills/rules | Refresh |
|---|---|---|---|
| Devin Cloud | plugin `kit/AGENTS.md` | plugin `kit/skills/` and `kit/rules/` | fetches `main` per session |
| Devin CLI/Desktop | plugin subfolder `kit/` | plugin contents | app startup; doctor updates stale SHA |
| Codex | `~/.codex/AGENTS.md` → `~/.ai-kit/kit/AGENTS.md` | marketplace plugin plus temporary fallback symlinks | launchd every six hours |

## Devin plugin

Install the repository plugin subfolder in personal or managed scope:

```bash
devin plugins install ChristianPrzybulinski/agent-rules-kit#kit
```

An install recorded without `#kit` keeps reading the old root: remove it (Customize → Plugins) and add it again with the source above, then Reindex. Run `devin plugins update ai-kit` to force a local refresh.

## Codex

Bootstrap registers the marketplace and plugin:

```bash
codex plugin marketplace add ChristianPrzybulinski/agent-rules-kit --ref main
codex plugin add ai-kit@ai-kit
```

The marketplace catalog stays at the repository root and points to `./kit`; `~/.codex/AGENTS.md` links to `~/.ai-kit/kit/AGENTS.md`. While [openai/codex#22078](https://github.com/openai/codex/issues/22078) remains open, installed plugin skills may not be exposed to the model, so `doctor.sh` maintains `~/.codex/skills/<name>` symlinks to `~/.ai-kit/kit/skills/<name>` and removes them once `codex debug prompt-input` exposes `ai-kit:*` skills. When only the desktop app is discoverable, doctor uses app-only mode and keeps the fallback active.

## Refresh and diagnosis

On macOS, launchd runs `platforms/tools/refresh.sh` at login and every six hours. `platforms/tools/doctor.sh` repairs clone, plugin and symlink state. Nothing refreshes at agent session start.
