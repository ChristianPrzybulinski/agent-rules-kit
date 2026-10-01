# platforms/install/ — installation into the tools

`all.sh` installs `agents/` into the tools and validates. Order: `third-party.sh --check` → `skills.sh` → `devin.sh` → `windsurf.sh` → `codex.sh` → legacy `~/.cursor/rules/*.mdc` cleanup → writes `~/.config/agent-rules-kit/{VERSION,LAYOUT_VERSION}` → `check.sh`.

```bash
platforms/install/all.sh          # installs everything
platforms/install/all.sh --clean  # deletes managed destinations first (layout change)
```

| Script | Destination | What it installs |
|---|---|---|
| `skills.sh` | `~/.agents/skills/<name>/` (Devin, Cursor, Codex) · `~/.codeium/windsurf/skills/<name>/` | flattened skills (whole directory) with an `.agent-rules-kit` marker — unmarked user/third-party folders untouched |
| `devin.sh` | `~/.config/devin/AGENTS.md` | always-on; removes legacy `~/.devin/rules/`, `~/.devin/global_rules.md` and kit-named folders in `~/.config/devin/skills/` |
| `windsurf.sh` | `~/.codeium/windsurf/memories/global_rules.md` | always-on |
| `codex.sh` | `~/.codex/AGENTS.md` | always-on; removes legacy kit-marked folders in `$CODEX_HOME/skills` |
| `devin-plugin.sh <out-dir>` | `<out-dir>` (CI: `devin-plugin` branch) | Devin plugin `ai-kit`: `.devin-plugin/plugin.json`, `AGENTS.md` (always-on), flattened `skills/<name>/`; not run by `all.sh` |
| `third-party.sh` | `agents/skills/vendor/` | vendors the lock's skills; `--check` only validates |
| `all.sh` | all + `~/.config/agent-rules-kit/` | orchestrates + records installed state |

Does not install to `~/.devin/global_rules.md` or `~/.claude/CLAUDE.md` (would duplicate AGENTS.md in the context). First time on the machine: `platforms/tools/bootstrap.sh`.
