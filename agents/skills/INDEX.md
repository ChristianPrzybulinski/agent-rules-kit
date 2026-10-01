# skills/ — invocable procedures, by type

Scope: how to execute a task step by step (`/name`), with inputs, outputs and "done when" — including the normative detail of each domain, which lives in the skill's `references/` when it does not fit in the SKILL.md. Fact → `../knowledge/`. Installed flattened by basename into `~/.agents/skills/` — skill names are unique across the whole kit.

| Type | Folder | Contains |
|---|---|---|
| core | [`core/`](core/INDEX.md) | session discipline, session review, evidence, response register, parallel work |
| quality | [`quality/`](quality/INDEX.md) | verification, investigation, characterization tests, vulnerabilities, secure development |
| development | [`development/`](development/INDEX.md) | stacks, code standards, asset import, protocol contract |
| documentation | [`documentation/`](documentation/INDEX.md) | project docs, session handoff |
| process | [`process/`](process/README.md) | SDD — 9 `sdd-*` steps |
| tooling | [`tooling/`](tooling/INDEX.md) | CLIs and services (gh, lfs, postgres, redis, docker, dbeaver, krita) + branching/versioning |
| vendor | [`vendor/`](vendor/INDEX.md) | third-party skills pinned by commit (see `../../platforms/kits/third-party/`) |

## All skills

| Skill | Type | When to use |
|---|---|---|
| `evidence` | core | evaluate a proposal, confidence <98%, skepticism |
| `sessions` | core | session start, long session, topic change |
| `session-review` | core | end of session: summary + at most one kit proposal (only with evidence) |
| `tokens` | core | response register (technical vs. text for people) |
| `parallelize` | core | batch independent calls, background long commands, fan out `[P]` tasks; what stays sequential |
| `skeptic` | quality | dubious claim → verdict with confidence |
| `validate-implementation` | quality | "is it done?" before a PR/closing a task |
| `vuln-scan` | quality | CVEs, secrets, OWASP before a PR/release |
| `characterization-tests` | quality | pin down current legacy behavior before refactoring |
| `secure-development` | quality | dependencies, auth, endpoints, sensitive data |
| `investigate` | development | bug/slowness/incident to root cause |
| `java-standards` | development | Java code, pom.xml |
| `godot-standards` | development | GDScript, nodes, scenes |
| `asset-import` | development | external sprites/tilesets/maps → Godot, with manifest |
| `protocol-contract` | development | create/evolve a client↔server message |
| `clean-code` | development | write/review production code |
| `simplicity` | development | design a solution, oversized PR, dependency choice |
| `testing` | development | create tests, coverage/mutation gates |
| `twelve-factor` | development | configure app, env vars, deploy |
| `clean-architecture` | development | module/layer, where a class lives |
| `ddd-and-patterns` | development | model a domain, choose a pattern |
| `update-docs` | documentation | README, CHANGELOG, ADR, semver |
| `session-handoff` | documentation | end of session, agent switch |
| `sdd-constitution` → `sdd-to-card` | process | new feature end to end (see `process/README.md`) |
| `github-cli` | tooling | branches, PRs, releases via `gh` |
| `git-lfs` | tooling | binaries, .gitattributes, quota |
| `branching-and-versioning` | tooling | branch, commit, release, `protocol_version` |
| `postgresql` | tooling | schema, migrations, diagnostics |
| `redis` | tooling | cache, session, light queue |
| `docker` | tooling | local compose, Dockerfile, diagnostics |
| `dbeaver` | tooling | inspect local Postgres |
| `krita` | tooling | pixel art and sprite retouching |
| `grill-me` / `grilling` | vendor | relentless interview to sharpen a plan (command only) |
| `skill-creator` | vendor | create/evaluate a skill |
| `find-skills` | vendor | discover an existing skill for a task |
| `frontend-design` | vendor | UI visual direction |
