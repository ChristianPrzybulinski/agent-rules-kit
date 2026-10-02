# skills/ — invocable procedures

Skills are flat by name and grouped here by their former type.

## Core

Session discipline and reasoning.

| Skill | Description |
|---|---|
| `parallelize` | Parallel planning for tool calls, long commands and [P] tasks. Use when work has independent steps. Not for product concurrency (skill testing). |
| `session-review` | Session closeout with evidence and one kit proposal. Use when work is delivered or a session closes. Not for handoff records (skill session-handoff). |
| `sessions` | Session scope and hygiene. Use when starting, changing topics or detecting a long session. Not for recording completed work (skill session-handoff). |
| `tokens` | Response register for code, e-mail, reports, README and governed docs. Use when writing long answers or text for humans. Not for doc policy (skill update-docs). |

## Quality

Verification and quality.

| Skill | Description |
|---|---|
| `characterization-tests` | Tests that pin current behavior of legacy or ported code. Use when refactoring or rebalancing a rule with no spec. Not for new behavior (skill testing). |
| `secure-development` | Security design for dependencies, auth, endpoints and sensitive data. Use when changing a trust boundary. Not for scanning changes (skill vuln-scan). |
| `skeptic` | Adversarial check of a claim or proposed fix. Use when the user suggests a solution, a claim is unproven, or confidence <98%. Not for bugs (skill investigate). |
| `validate-implementation` | Completion verdict against a request or FEAT. Use when asking “is it done?” or preparing a PR. Not for fixing failures (skill sdd-implement). |
| `vuln-scan` | Scan for CVEs, secrets and changed endpoints. Use when preparing a sensitive PR, release or requested audit. Not for security design (skill secure-development). |

## Development

Development by stack.

| Skill | Description |
|---|---|
| `asset-import` | Godot asset import with manifests and reproducible transforms. Use when bringing sprites, tilesets or maps into Godot. Not for drawing art (skill krita). |
| `clean-architecture` | Clean Architecture layer and port placement. Use when defining layers, ports or where a class lives. Not for pattern choice (skill ddd-and-patterns). |
| `clean-code` | Code rules for names, functions and comments. Use when naming, editing functions, writing comments or reviewing code. Not for test policy (skill testing). |
| `ddd-and-patterns` | Tactical DDD and pattern selection. Use when defining an aggregate or choosing a design pattern. Not for layer placement (skill clean-architecture). |
| `godot-standards` | Godot 2D and typed GDScript standards. Use when editing *.gd, *.tscn, project.godot or GDScript scenes. Not for asset import (skill asset-import). |
| `investigate` | Root-cause investigation with reproduction. Use when a bug, slow behavior or incident has no named cause. Not for implementing fixes (skill sdd-implement). |
| `java-standards` | Java 25, Spring/Quarkus and JUnit standards. Use when editing *.java, pom.xml, Spring/Quarkus code or JUnit tests. Not for general test policy (skill testing). |
| `protocol-contract` | Client↔server contracts. Use when adding a message or field, changing a payload or fixing a client/server mismatch. Not for transport choice (skill sdd-plan). |
| `simplicity` | YAGNI ladder for the smallest change. Use when choosing a dependency, reviewing an oversized PR or adding an abstraction. Not for test gates (skill testing). |
| `testing` | Test policy and gates. Use when setting coverage/mutation gates or deciding what not to test. Not for legacy tests (skill characterization-tests). |
| `twelve-factor` | Twelve-Factor application configuration. Use when changing config, env vars, deploy behavior or Docker app config. Not for container mechanics (skill docker). |

## Documentation

Project documentation.

| Skill | Description |
|---|---|
| `session-handoff` | Records the handoff between work sessions — what was done with evidence, what is pending, decisions made/open and the next session's first concrete task. Use when closing a long session, before switching agent/tool, or when context will be lost. Do not use for the end-of-session summary and kit review (skill session-review). |
| `update-docs` | Updates README, CHANGELOG, ADRs and semantic versioning. Use when closing a visible change, editing docs or preparing a release. Do not use for spec artifacts — they follow the `spec-*` templates and schemas. |

## Process

Spec-Driven Development procedures.

| Skill | Description |
|---|---|
| `sdd-analyze` | SDD step 3 — cross-artifact consistency report. Use when FEAT/REQ/DEC/plan/tasks need gap checks. Not for spec quality (skill sdd-audit). |
| `sdd-audit` | SDD step 4 — spec quality checklist. Use when a clarified FEAT needs testability, security and completeness checks. Not for consistency (skill sdd-analyze). |
| `sdd-clarify` | SDD step 2 — resolve ambiguous FEAT criteria. Use when a FEAT has open questions or vague terms. Not for quality auditing (skill sdd-audit). |
| `sdd-constitution` | SDD step 0 — project constitution and spec index. Use when starting a project or changing principles. Not for one feature (skill sdd-specify). |
| `sdd-implement` | SDD step 7 — task-by-task Red-Green-Refactor delivery. Use when a FEAT has ordered tasks. Not for completion verdicts (skill validate-implementation). |
| `sdd-plan` | SDD step 5 — technical FEAT plan and decisions. Use when clarification and audit are complete. Not for task breakdown (skill sdd-tasks). |
| `sdd-specify` | SDD step 1 — feature and requirement specification. Use when a described feature needs FEAT/REQ criteria. Not for open questions (skill sdd-clarify). |
| `sdd-tasks` | SDD step 6 — dependency-ordered implementation tasks. Use when a FEAT has an approved technical plan. Not for execution (skill sdd-implement). |
| `sdd-to-card` | SDD step 9 — sync a FEAT to GitHub Issues/Projects. Use when opening, updating or closing its card. Not for PR operations (skill github-cli). |

## Tooling

Tools and services.

| Skill | Description |
|---|---|
| `branching-and-versioning` | Trunk-based with main + feature/*, feature flags with expiry, Conventional Commits, SemVer and a separate protocol version. Use when creating a branch, committing, opening a PR, publishing a release or changing the contract. Do not use for `gh` command mechanics (skill github-cli). |
| `dbeaver` | DBeaver to inspect the local PostgreSQL — connection via .env, exporting/importing test data, generating DDL/ER for documentation, without becoming a source of schema change (that is Flyway). Use when the human needs to see/edit data or generate a diagram. Do not use to change the schema (Flyway, skill postgresql). |
| `docker` | Docker and Compose for a reproducible local environment — Postgres/Redis compose with healthchecks, multi-stage Dockerfile for Java, volumes, networks, .env, diagnostics. Use when creating/changing local infra, a Dockerfile, or when a service won't start. Do not use for application config/env policy (skill twelve-factor) or Postgres/Redis internals (skills postgresql, redis). |
| `git-lfs` | Configures and audits Git LFS in a repository — .gitattributes by type/size, migrating already-committed binaries, quota verification and files that escaped LFS. Use when starting a repo with assets, adding a new binary type, or when `git status` shows a large binary. Do not use for branching or release policy (skill branching-and-versioning) or `gh` mechanics (skill github-cli). |
| `github-cli` | Uses `gh` and git for branches, commits, PRs, releases and reviews — authentication, PR body with what/why/how-to-test, merge only after checks. Use when creating branches, commits, PRs or releases. Do not use for the branching/SemVer policy (skill branching-and-versioning) or LFS (skill git-lfs). |
| `krita` | Krita for pixel art and sprite retouching — document setup (size, no antialiasing, indexed palette), exporting PNG for Godot preserving transparency, spritesheets, and what to automate by script instead of the GUI. Use when preparing/fixing 2D art or defining an export workflow. Do not use to import finished art into Godot (skill asset-import). |
| `postgresql` | PostgreSQL as the source of truth — modeling, Flyway migrations, indexes, transactions/isolation, idempotency, backup/restore and diagnostics (EXPLAIN, locks, bloat). Use when creating/changing a schema, investigating slowness or planning persistence. Do not use for cache/ephemeral data (skill redis) or GUI inspection (skill dbeaver). |
| `redis` | Redis as cache/ephemeral — when to use it (and when not), keys with TTL, pub/sub for presence, rate limiting, short locks; never the source of truth for inventory, progression or economy. Use when proposing cache, session, a light queue or coordination. Do not use for durable data or the source of truth (skill postgresql). |

## Vendor

Third-party skills are pinned by commit in `platforms/kits/third-party/skills.lock`; do not edit them directly.

| Skill | Description |
|---|---|
| `find-skills` | Helps users discover and install agent skills when they ask questions like "how do I do X", "find a skill for X", "is there a skill that can...", or express interest in extending capabilities. This skill should be used when the user is looking for functionality that might exist as an installable skill. |
| `frontend-design` | Guidance for distinctive, intentional visual design when building new UI or reshaping an existing one. Helps with aesthetic direction, typography, and making choices that don't read as templated defaults. |
| `grilling` | Grill the user relentlessly about a plan, decision, or idea. Use when the user wants to stress-test their thinking, or uses any 'grill' trigger phrases. |
| `skill-creator` | Create new skills, modify and improve existing skills, and measure skill performance. Use when users want to create a skill from scratch, edit, or optimize an existing skill, run evals to test a skill, benchmark skill performance with variance analysis, or optimize a skill's description for better triggering accuracy. |
