# tools/ — kit lifecycle on the machine

| File | Scope | When to use |
|---|---|---|
| `bootstrap.sh` | clones the kit, connects agent plugins, installs launchd, then runs doctor | first setup on a machine |
| `refresh.sh` | fast-forwards the main clone and upgrades the Codex marketplace | scheduled refresh or manual update |
| `doctor.sh` | verifies clone, plugins, symlinks, legacy cleanup and context budgets | diagnose setup or after refresh |
| `smoke.sh` | runs bootstrap and doctor against isolated throwaway homes | after lifecycle changes; in CI |
| `vendor.sh` | installs pinned third-party skills; `--check` verifies the lock | update or verify vendored skills |
| `check.sh` | validates the kit; `--spec <dir>` validates project specs | after any kit change; in CI |
| `sync-project.sh` | copies spec validation files into a project; `--check` compares | initialize or refresh project spec CI |
