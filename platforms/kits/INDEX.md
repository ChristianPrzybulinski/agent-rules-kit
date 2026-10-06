# kits/ — ready-to-copy files for projects

Scope: configuration and infra templates a project copies (not read by the agent as instructions — plugin instructions are in `plugins/core/AGENTS.md`, `plugins/*/rules/`, and `plugins/*/skills/`).

| Kit | Contents | When to use |
|---|---|---|
| `docker/` | PostgreSQL + Mailpit compose (an optional Valkey service commented out), multi-stage Dockerfile.java, init SQL, .env.example | project local infra |
| `git-lfs/` | ready `.gitattributes` | before the first binary in the repo |
| `github/` | workflows (spec-lint, gitleaks, pr-contract, ci-java, ci-godot), PR template, CODEOWNERS, labels + sync, dependabot | every new repo |
| `godot/` | Godot `.gitignore`, editor hints, `make_spritesheet.py` | Godot project |
| `java-maven/` | parent pom with gates, toolchains, suppressions, `.java-version` | Java/Maven project |
| `launchd/` | six-hour AI Kit refresh agent for macOS | installed by `platforms/tools/bootstrap.sh` |
| `sdd/` | `init-spec.sh` — creates `docs/spec/` from `plugins/architect-sdd/templates/spec-*` | spec bootstrap in the project |
| `third-party/` | `skills.lock` — external skills pinned by commit | regenerate vendor skills under `plugins/<plugin>/skills/` |
