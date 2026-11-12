# kits/ — ready-to-copy files for projects

Scope: configuration and infra templates a project copies (not read by the agent as instructions — plugin instructions are in `plugins/core/AGENTS.md`, `plugins/*/rules/`, and `plugins/*/skills/`).

| Kit | Contents | When to use |
|---|---|---|
| `devin/` | `environment.{godot,java,docs}.yaml`, `snapshot-checklist.md`, `playbooks/` (`implement-issue`, `fix-round`, `devin-review-autofix`) | Devin Cloud snapshot + environment; review-loop children |
| `docker/` | PostgreSQL + Mailpit compose (an optional Valkey service commented out), multi-stage Dockerfile.java, init SQL, .env.example | project local infra |
| `git-lfs/` | ready `.gitattributes` | before the first binary in the repo |
| `github/` | workflows (spec-lint, gitleaks, pr-contract, ci-java, ci-godot), PR template, CODEOWNERS, labels + sync, dependabot, root REVIEW.md | every new repo |
| `godot/` | Godot `.gitignore`, editor hints, `make_spritesheet.py` | Godot project |
| `java-maven/` | parent pom with gates, toolchains, suppressions, `.java-version` | Java/Maven project |
| `launchd/` | six-hour AI Kit refresh agent for macOS | installed by `platforms/tools/bootstrap.sh` |
| `review-loop/` | verdict schema, example config (proof allowlist, poll interval, 2 flagged rounds then needs-human, repo list), README with the loop-tool decision | project running the review loop (its skills live in that project) |
| `sdd/` | `init-spec.sh` — creates `docs/spec/` from `plugins/sdd/templates/spec-*` | spec bootstrap in the project |
| `third-party/` | `skills.lock` — external skills pinned by commit | regenerate vendor skills under `plugins/<plugin>/skills/` |
