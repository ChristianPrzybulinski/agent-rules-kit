# kits/ — ready-to-copy files for projects

Scope: configuration and infra templates a project copies (not read by the agent as instructions — plugin instructions are in `plugins/guardrails/AGENTS.md`, `plugins/*/rules/`, and `plugins/*/skills/`).

| Kit | Contents | When to use |
|---|---|---|
| `docker/` | PostgreSQL + Mailpit compose (an optional Valkey service commented out), init SQL, .env.example | project local infra |
| `git-lfs/` | ready `.gitattributes` | before the first binary in the repo |
| `github/` | workflows (spec-lint, gitleaks CLI, pr-contract, ci-java, ci-godot), PR template, labels + sync, root REVIEW.md | every new repo |
| `godot/` | Godot `.gitignore`, the keyed-CSV merge driver `keyed_csv_merge.py` | Godot project |
| `java-maven/` | parent pom with gates, toolchains, suppressions, `.java-version` | Java/Maven project |
| `just/` | one `just` module per profile (`godot`, `java`, `python`, `docs`) with the standard recipes `test`, `verify`, `fmt`, `lint` and `run` where it fits; `sync-project.sh` writes the profile's module as `kit.just` in each profile folder (KIT-074) | every project; the AGENTS and CI templates call these recipes |
| `launchd/` | six-hour AI Kit refresh agent for macOS | installed by `platforms/tools/bootstrap.sh` |
| `review-loop/` | README only: where the loop lives (`dev-game-studio/review-loop`) and how its children preload kit skills | project running the review loop (its skills live in that project) |
| `sdd/` | `init-spec.sh` — creates `docs/spec/` from `plugins/guardrails/templates/spec-*` | spec bootstrap in the project |
| `third-party/` | `skills.lock` — external skills pinned by commit | regenerate vendor skills under `plugins/<plugin>/skills/` |
