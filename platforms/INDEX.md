# platforms/ — what runs on the machine and in CI

Scope: executables and tool configuration. Nothing here is an instruction for the agent; the agent only **runs** what is here (install, validate, update).

| Folder | Scope | Main entry |
|---|---|---|
| [`install/`](install/README.md) | installs `agents/` into the tools; vendors pinned external skills | `all.sh` |
| [`tools/`](tools/INDEX.md) | kit lifecycle on the machine | `bootstrap.sh` (1st time) · `refresh.sh` (every session) · `check.sh` (validate) |
| [`ci/`](ci/README.md) | schemas for every frontmatter and for project specs; validation scripts used by `check.sh` and by the workflows | `validations/check_kit.py` · `validations/check_spec.py` |
| [`kits/`](kits/INDEX.md) | ready-to-copy files for projects (Maven parent, Compose, workflows, LFS, labels, external skills lock) | per kit |

## Where each thing is installed

| Destination | Content | Managed by |
|---|---|---|
| `~/.config/devin/AGENTS.md` · `~/.config/devin/skills/<name>/` · `~/.devin/rules/` | Devin | `install/devin.sh` |
| `~/.cursor/rules/*.mdc` | Cursor (converted rules) | `install/cursor.sh` |
| `~/.codeium/windsurf/memories/global_rules.md` | Windsurf | `install/windsurf.sh` |
| `~/.codex/AGENTS.md` · `~/.agents/skills/<name>/` | Codex | `install/codex.sh` |
| `~/.config/agent-rules-kit/{VERSION,LAYOUT_VERSION}` | installed state, read by `refresh.sh` | `install/all.sh` |

A `LAYOUT_VERSION` different from the installed one → `refresh.sh` deletes the managed destinations and reinstalls everything. A different `VERSION` → reinstall only. Equal → exits silently.
