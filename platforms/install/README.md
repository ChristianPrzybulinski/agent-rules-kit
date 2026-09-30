# platforms/install/ — installation into the tools

`all.sh` installs `agents/` into the tools and validates. Order: `third-party.sh --check` → `devin.sh` → `cursor.sh` → `windsurf.sh` → `codex.sh` → writes `~/.config/agent-rules-kit/{VERSION,LAYOUT_VERSION}` → `check.sh`.

```bash
platforms/install/all.sh          # installs everything
platforms/install/all.sh --clean  # deletes managed destinations first (layout change)
```

| Script | Destination | What it installs |
|---|---|---|
| `devin.sh` | `~/.config/devin/AGENTS.md` · `~/.devin/rules/` · `~/.config/devin/skills/<name>/` | always-on, per-domain rules, flattened skills (whole directory) |
| `cursor.sh` | `~/.cursor/rules/<dom>-<name>.mdc` | converted rules (Cursor frontmatter) |
| `windsurf.sh` | `~/.codeium/windsurf/memories/global_rules.md` | always-on |
| `codex.sh` | `~/.codex/AGENTS.md` · `~/.agents/skills/<name>/` | always-on + skills with an `.agent-rules-kit` marker (`.system` and user content untouched) |
| `third-party.sh` | `agents/skills/vendor/` | vendors the lock's skills; `--check` only validates |
| `all.sh` | all + `~/.config/agent-rules-kit/` | orchestrates + records installed state |

Does not install to `~/.devin/global_rules.md` or `~/.claude/CLAUDE.md` (would duplicate AGENTS.md in the context). First time on the machine: `platforms/tools/bootstrap.sh`.
