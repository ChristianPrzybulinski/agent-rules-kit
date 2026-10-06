# tools/ — kit lifecycle on the machine

| File | Scope | When to use |
|---|---|---|
| `bootstrap.sh` | clones the kit, connects agent plugins, installs launchd, then runs doctor | first setup on a machine |
| `refresh.sh` | fast-forwards main and updates Codex/Claude marketplaces and plugins | scheduled refresh or manual update |
| `doctor.sh` | verifies plugins/symlinks, merges Devin import policy, cleans legacy state and checks budgets; `AI_KIT_USER_RULES=0` skips user-level rule symlinks | diagnose setup or after refresh |
| `smoke.sh` | runs bootstrap and doctor against isolated throwaway homes | after lifecycle changes; in CI |
| `vendor.sh` | installs pinned third-party skills; `--check` verifies the lock | update or verify vendored skills |
| `check.sh` | validates the kit and Claude manifests; `--spec <dir>` validates project specs | after any kit change; in CI |
| `sync-project.sh` | copies spec validation files into a project and generates `CLAUDE.md` (imports `AGENTS.md`), `.claude/settings.json` (kit marketplace, `enabledPlugins` per profile `godot|java|docs`, inferred or `--profile`) and `.claude/rules/<plugin>-<rule>.md` (the profile's path rules, marked generated); `--check` compares all of them and scans the repo's `*.md` for obsolete kit paths; `--workflow <file>` names the CI file that runs `check_spec.py` (any name is accepted if it does) | initialize or refresh a project; in the project's CI |
