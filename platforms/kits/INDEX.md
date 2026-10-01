# kits/ — ready-to-copy files for projects

Scope: configuration and infra templates a project copies (not read by the agent as instructions — instructions are in `AGENTS.md`, `rules/`, and `skills/`).

| Kit | Contents | When to use |
|---|---|---|
| `docker/` | PostgreSQL+Redis compose, multi-stage Dockerfile.java, init SQL, .env.example | project local infra |
| `git-lfs/` | ready `.gitattributes` | before the first binary in the repo |
| `github/` | workflows (spec-lint, gitleaks, ci-java, ci-godot), PR template, CODEOWNERS, labels + sync, dependabot | every new repo |
| `godot/` | Godot `.gitignore`, editor hints, `make_spritesheet.py` | Godot project |
| `java-maven/` | parent pom with gates, toolchains, suppressions, `.java-version` | Java/Maven project |
| `sdd/` | `init-spec.sh` — creates `docs/spec/` from `templates/spec-*` | spec bootstrap in the project |
| `third-party/` | `skills.lock` — external skills pinned by commit | regenerate vendor skills under `skills/` |
