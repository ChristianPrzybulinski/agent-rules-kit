# rules/ — normative by domain

Scope: what the agent MUST/MUST NOT do, on demand (≤60 lines each). Always-on summary: `../AGENTS.md`. Dated facts do not go here — they go in `../knowledge/`.

| Domain | Rule | When to load |
|---|---|---|
| `architecture/` | `clean-architecture.md` | create module/layer, decide where a class lives |
| `architecture/` | `ddd-and-patterns.md` | model a domain, choose a pattern (when to use / when not) |
| `core/` | `evidence.md` | evaluate a proposal, confidence <98%, skepticism |
| `core/` | `sessions.md` | session start, long session, out-of-context request |
| `core/` | `tokens.md` | choose response register (technical vs. text for people) |
| `development/` | `clean-code.md` | write/review production code |
| `development/` | `simplicity.md` | design a solution, oversized PR, decide if a test is needed |
| `development/` | `testing.md` | create tests, configure coverage/mutation gates |
| `development/` | `twelve-factor.md` | configure app, Docker, env vars, deploy |
| `documentation/` | `documentation.md` | README, changelog, ADR, versioning |
| `documentation/` | `living-docs.md` | close task/PR — docs updated in the same commit |
| `git/` | `branching-and-versioning.md` | branch, commit, PR, release, protocol version |
| `git/` | `git-lfs-and-binaries.md` | add assets/binaries/exports to the repo |
| `git/` | `github-cli.md` | workflows with `gh` and git |
| `godot/` | `godot-2d.md` | `*.gd`, `*.tscn`, `project.godot` |
| `java/` | `build-and-dependencies.md` | `pom.xml`, Maven project, quality plugins |
| `java/` | `java.md` | modern Java code, Clean Code |
| `security/` | `secure-development.md` | dependencies, auth, endpoints, sensitive data |
