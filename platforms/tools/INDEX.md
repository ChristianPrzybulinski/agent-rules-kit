# tools/ — kit lifecycle on the machine

| File | Scope | When to use |
|---|---|---|
| `bootstrap.sh` | clones `~/.ai-kit` (gh, https fallback) and installs | first time on the machine |
| `refresh.sh` | `git pull --ff-only` + reinstalls if VERSION/LAYOUT_VERSION changed (layout → `--clean`) | session start (`--quiet` exits silently) |
| `check.sh` | validates the kit (`check_kit.py`); `--spec <dir>` validates a project's `docs/spec` | after any kit change; in CI |
| `sync-project.sh` | copies `check_spec.py` + spec schemas + `spec-lint.yml` into a project's `.github/`; `--check` compares | new project (via `init-spec.sh`) or after changing the validator |
| `install-smoke.sh` | installs into a throwaway `HOME` twice, plants unmarked user skills, runs `--clean` and asserts nothing of the user is lost | after touching `platforms/install/`; in CI |

Installed state: `~/.config/agent-rules-kit/{VERSION,LAYOUT_VERSION}`.
