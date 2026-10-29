# tools/ — kit lifecycle on the machine

| File | Scope | When to use |
|---|---|---|
| `bootstrap.sh` | clones the kit, connects agent plugins, installs launchd, then runs doctor | first setup on a machine |
| `refresh.sh` | fast-forwards main and updates Codex/Claude marketplaces and plugins; reinstalls a Claude plugin whose cache differs from the kit (KIT-013) | scheduled refresh or manual update |
| `doctor.sh` | verifies plugins/symlinks, warns on a stale Claude plugin cache, merges Devin import policy, cleans legacy state and checks budgets; `AI_KIT_USER_RULES=1` restores user-level rule symlinks (default 0: repos carry `.claude/rules`) | diagnose setup or after refresh |
| `smoke.sh` | runs bootstrap and doctor against isolated throwaway homes | after lifecycle changes; in CI |
| `vendor.sh` | installs pinned third-party skills; `--check` verifies the lock | update or verify vendored skills |
| `kpi.py` | per-batch review-loop KPIs from a `ledger.csv` | after each loop batch; before and after a kit rule change |
| `check.sh` | validates the kit and Claude manifests; `--spec <dir>` validates project specs | after any kit change; in CI |
| `sync-project.sh` | copies spec validation files into a project that has `docs/spec` and generates `CLAUDE.md` (imports `AGENTS.md`), `.claude/settings.json` (kit marketplace, `enabledPlugins` per profile `godot|java|docs`, inferred or `--profile`; a comma list such as `docs,godot:client,java:server` syncs the union for a monorepo, `:<dir>` scoping that profile's rule globs) and `.claude/rules/<plugin>-<rule>.md` (the profile's path rules, marked generated); `--check` compares all of them and scans the repo's `*.md` for obsolete kit paths; `--workflow <file>` names the CI file that runs `check_spec.py` (any name is accepted if it does); `--vendor-skills` copies the profile's skills into `.claude/skills/` with a hashed `KIT_MANIFEST.json` | initialize or refresh a project; in the project's CI |
