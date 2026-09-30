# skills/ — invocable procedures, by type

Scope: how to execute a task step by step (`/name`), with inputs, outputs and "done when". Generic rule → `../rules/`; fact → `../knowledge/`. Devin installs flattened by basename — skill names are unique across the whole kit.

| Type | Folder | Contains |
|---|---|---|
| quality | [`quality/`](quality/INDEX.md) | verification, investigation, characterization tests, vulnerabilities |
| development | [`development/`](development/INDEX.md) | stacks, asset import, protocol contract |
| documentation | [`documentation/`](documentation/INDEX.md) | project docs, session handoff |
| process | [`process/`](process/README.md) | SDD — 9 `sdd-*` steps |
| tooling | [`tooling/`](tooling/INDEX.md) | CLIs and services (gh, lfs, postgres, redis, docker, dbeaver, krita) |
| vendor | [`vendor/`](vendor/INDEX.md) | third-party skills pinned by commit (see `../../platforms/kits/third-party/`) |

## All skills

| Skill | Type | When to use |
|---|---|---|
| `skeptic` | quality | dubious claim → verdict with confidence |
| `validate-implementation` | quality | "is it done?" before a PR/closing a task |
| `vuln-scan` | quality | CVEs, secrets, OWASP before a PR/release |
| `characterization-tests` | quality | pin down current legacy behavior before refactoring |
| `investigate` | development | bug/slowness/incident to root cause |
| `java-standards` | development | Java code, pom.xml |
| `godot-standards` | development | GDScript, nodes, scenes |
| `asset-import` | development | external sprites/tilesets/maps → Godot, with manifest |
| `protocol-contract` | development | create/evolve a client↔server message |
| `update-docs` | documentation | README, CHANGELOG, ADR, semver |
| `session-handoff` | documentation | end of session, agent switch |
| `sdd-constitution` → `sdd-to-card` | process | new feature end to end (see `process/README.md`) |
| `github-cli` | tooling | branches, PRs, releases via `gh` |
| `git-lfs` | tooling | binaries, .gitattributes, quota |
| `postgresql` | tooling | schema, migrations, diagnostics |
| `redis` | tooling | cache, session, light queue |
| `docker` | tooling | local compose, Dockerfile, diagnostics |
| `dbeaver` | tooling | inspect local Postgres |
| `krita` | tooling | pixel art and sprite retouching |
| `grill-me` / `grilling` | vendor | relentless interview to sharpen a plan (command only) |
| `skill-creator` | vendor | create/evaluate a skill |
| `find-skills` | vendor | discover an existing skill for a task |
| `frontend-design` | vendor | UI visual direction |
