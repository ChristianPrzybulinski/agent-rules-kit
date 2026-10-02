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
| `asset-import` | Imports sprites, animations, tilesets and maps into a Godot 2D project from external originals (legacy archive, Krita, Aseprite) deterministically, non-destructively and traceably — originals untouched, derivatives with a manifest (origin, hash, dimensions, pivot, aliases), rejected-items report for human review. Use when bringing art into the project or reprocessing a batch. Do not use to draw/edit art (krita skill). |
| `clean-architecture` | Clean Architecture details — layers, dependency rule, ports/adapters, DTOs, exceptions. Use when creating a module, a layer or deciding where a class lives. Do not use for choosing a design pattern (skill ddd-and-patterns) or naming detail (skill clean-code). |
| `clean-code` | Clean Code details — names, functions, classes, comments, tests. Use when writing or reviewing production code. Do not use for test policy (skill testing) or layer boundaries (skill clean-architecture). |
| `ddd-and-patterns` | Tactical DDD and a design-patterns catalog with "when to use / when not". Use when modeling a domain, choosing a pattern or reviewing a module's architecture. Do not use for layer boundaries (skill clean-architecture). |
| `godot-standards` | Applies Godot 2D standards — statically typed GDScript, scene composition, signals, physics separation, versioned saves. Use on `*.gd`, `*.tscn` or `project.godot`. Do not use for importing external art (skill asset-import) or pixel-art editing (skill krita). |
| `investigate` | Investigates a bug, regression, performance problem or incident to a named root cause, with reproduction before any fix. Use when something "doesn't work", is slow, or failed in production/CI. Do not use to implement the fix (that returns to the normal flow with a failing test first). |
| `java-standards` | Applies modern Java standards — style (`var`, `Optional`, `record`, `sealed`), Clean Architecture packages, Spring/Quarkus, JUnit 5 tests. Use on `*.java` or `pom.xml`. Do not use for build/module/plugin gates detail (`references/build-and-dependencies.md`) or the general test policy (skill testing). |
| `protocol-contract` | Creates or evolves a client↔server contract message (command, event, response, error) with versioning, testable examples and compatibility rules. Use when adding/changing a field, creating a new message, or when client and server disagree about a payload. Do not use to decide transport/serialization (that is a DEC). |
| `simplicity` | Simplicity ladder (pragmatic YAGNI) — when not to write code, when a port/interface is justified, how to mark deliberate simplifications and how to report what was skipped. Use when designing a solution, reviewing an oversized PR, choosing a dependency or deciding whether a test is needed. Do not use for domain test gates (skill testing). |
| `testing` | Testing policy — 100% line/branch coverage and mutation ≥80% in the domain, happy+sad integration pairs, what not to test. Use when creating/changing tests or configuring build gates. Do not use for pinning the current behavior of legacy code before refactoring (skill characterization-tests). |
| `twelve-factor` | Twelve-Factor App applied to Java services and local tools — per-environment config, stateless processes, logs as a stream, dev/prod parity. Use when configuring an application, Docker, env vars or deploy. Do not use for local infra mechanics (skill docker). |

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
| `sdd-analyze` | SDD step 3 — consistency analysis across FEAT, REQs, DECs, plan and tasks - contradictions, gaps, orphan requirements, criteria without a task, tasks without a criterion. Read-only; produces a report. Use after clarify and after plan/tasks. Do not use to judge spec quality (skill sdd-audit) or to validate delivered code (skill validate-implementation). |
| `sdd-audit` | SDD step 4 — spec quality audit with a checklist - testability, completeness, security, data, errors, compatibility, observability. Produces a gap list to fix before planning. Use when the FEAT is clarified. Do not use for cross-artifact consistency (skill sdd-analyze) or to resolve open questions (skill sdd-clarify). |
| `sdd-clarify` | SDD step 2 — resolves a FEAT's [NEEDS CLARIFICATION] markers with objective questions (2-4 options each) to the product, incorporates the answers into the spec and moves status to clarified. Use when the FEAT has open questions or ambiguous criteria. Do not use to write the FEAT from scratch (skill sdd-specify) or to audit its quality (skill sdd-audit). |
| `sdd-constitution` | SDD step 0 — creates (or reviews) the project constitution - the repo's AGENTS.md with verifiable principles and docs/spec/spec.md with vision, scope, glossary and index. Use once per new project, or when principles change. Do not use for a single feature (skill sdd-specify) or to edit the kit's own AGENTS.md. |
| `sdd-implement` | SDD step 7 — executes a FEAT's tasks one by one (Red→Green→Refactor), on branch feature/FEAT-nnn, updating task states, docs and CHANGELOG; stops on a blocker and invents nothing. Use after tasks. Do not use before tasks exist (skill sdd-tasks) or to issue the done verdict (skill validate-implementation). |
| `sdd-plan` | SDD step 5 — technical plan for a clarified, audited FEAT - modules touched, domain model, contract, persistence/migration, feature flag, test strategy, risks; creates DEC-nnn for decisions with a rejected alternative. Status becomes planned. Use after sdd-audit, before sdd-tasks. Do not use to break the plan into tasks (skill sdd-tasks) or before clarify and audit are done. |
| `sdd-specify` | SDD step 1 — turns a feature description into FEAT-nnn (the what and why, not the how) and its linked REQ-F/REQ-NF, with testable acceptance criteria. Use when starting any new feature. Do not use to refine an existing FEAT (skill sdd-clarify) or to record a technical decision alone (DEC via sdd-plan). |
| `sdd-tasks` | SDD step 6 — breaks a FEAT's plan into small tasks ordered by dependency, each with a verifiable completion criterion and an associated test. Use after plan; the output is the Tasks section in the FEAT. Do not use to execute the tasks (skill sdd-implement) or when the FEAT has no Plan section (skill sdd-plan). |
| `sdd-to-card` | SDD step 9 — syncs a FEAT with a GitHub card (Issue + Project) via gh - creates the issue if missing, updates title/body/labels/status from the frontmatter, writes the number into the FEAT's card field. Use after specify (open) and after validate/merge (close). Do not use for branches, commits or PRs (skill github-cli). |

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
