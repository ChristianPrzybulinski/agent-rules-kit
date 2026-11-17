# kits/ — ready-to-copy files for projects

Scope: configuration and infra templates a project copies (not read by the agent as instructions — plugin instructions are in `plugins/guardrails/AGENTS.md`, `plugins/*/rules/`, and `plugins/*/skills/`).

| Kit | Contents | When to use |
|---|---|---|
| `docker/` | PostgreSQL + Mailpit compose (an optional Valkey service commented out), init SQL, .env.example | project local infra |
| `git-lfs/` | ready `.gitattributes` | before the first binary in the repo |
| `github/` | workflows (spec-lint, gitleaks CLI, pr-contract, ci-java, ci-godot), PR template, labels + sync, root REVIEW.md | every new repo |
| `godot/` | Godot `.gitignore`, the keyed-CSV merge driver `keyed_csv_merge.py` (git runs it from the installed kit, KIT-081 stage 1b) | Godot project |
| `java-maven/` | parent pom with gates, toolchains, suppressions, `.java-version` | Java/Maven project |
| `just/` | one `just` module per profile (`godot`, `java`, `python`, `docs`) with the standard recipes `test`, `verify`, `fmt`, `lint` and `run` where it fits; skill `sdd-implement` runs a folder's recipe from the installed kit, `just -f ~/.ai-kit/platforms/kits/just/<stack>.just -d <folder> <recipe>`, for the folder's stack in the project profile (KIT-074; KIT-085: no project justfile) | every project; the AGENTS and CI templates call these recipes |
| `launchd/` | six-hour AI Kit refresh agent for macOS | installed by `platforms/tools/bootstrap.sh` |
| `review-loop/` | README only: where the loop lives (`dev-game-studio/review-loop`) and how its children preload kit skills | project running the review loop (its skills live in that project) |
| `sdd/` | `init-spec.sh` — creates `docs/spec/` from `plugins/guardrails/templates/spec-*` | spec bootstrap in the project |
