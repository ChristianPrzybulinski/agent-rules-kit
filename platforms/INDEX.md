# platforms/ — what runs on the machine and in CI

Scope: executable lifecycle, validation and ready-to-copy project configuration.

| Folder | Scope | Main entry |
|---|---|---|
| [`tools/`](tools/INDEX.md) | bootstrap, refresh, diagnostics, validation and vendoring | `bootstrap.sh` · `doctor.sh` · `check.sh` |
| [`ci/`](ci/README.md) | schemas and validation scripts used locally and in CI | `validations/check_kit.py` · `validations/check_spec.py` |
| [`kits/`](kits/INDEX.md) | project configuration, workflows, launchd and external-skill lock | per kit |

## How agents consume v6

| Agent | Always-on | Skills and rules | Refresh |
|---|---|---|---|
| Devin Cloud | plugin `AGENTS.md` | plugin `skills/`, `rules/`, templates and references | fetches `main` per session |
| Devin CLI/Desktop | plugin `AGENTS.md` | plugin contents | app startup; `doctor.sh` updates a stale plugin SHA |
| Codex | `~/.codex/AGENTS.md` symlink | marketplace plugin plus temporary skill symlinks for #22078 | launchd every six hours via `refresh.sh` |
