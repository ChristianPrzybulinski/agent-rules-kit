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
| `session-handoff` | Session handoff record with evidence and next action. Use when switching agent/session or leaving pending work. Not for session summary (skill session-review). |
| `update-docs` | Project documentation closure. Use when updating README, CHANGELOG, Javadoc, ADR or release notes. Not for feature specs (skill sdd-specify). |

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
| `branching-and-versioning` | Branch, commit, PR and release policy. Use when creating a branch, flag, commit, PR, SemVer release or tag. Not for `gh` commands (skill github-cli). |
| `dbeaver` | DBeaver GUI inspection. Use when inspecting a database, exporting test data or drawing an ER diagram. Not for schema changes (skill postgresql). |
| `docker` | Docker and Compose workflow. Use when editing compose, a Dockerfile or diagnosing a container that will not start. Not for app config (skill twelve-factor). |
| `git-lfs` | Git LFS policy. Use when editing .gitattributes, adding/migrating a large binary or checking quota. Not for branch policy (skill branching-and-versioning). |
| `github-cli` | `gh` PR workflow. Use when writing a PR body, checking reviews, merging or publishing a release. Not for branch policy (skill branching-and-versioning). |
| `krita` | Krita pixel-art workflow. Use when editing pixel art, retouching sprites or defining sprite export. Not for Godot import (skill asset-import). |
| `postgresql` | PostgreSQL persistence rules. Use when changing a schema, migration or index, running EXPLAIN, or diagnosing locks. Not for cache data (skill redis). |
| `redis` | Redis ephemeral-data rules. Use when designing cache keys/TTL, rate limits, pub/sub or short locks. Not for durable data (skill postgresql). |

## Vendor

Third-party skills are pinned by commit in `platforms/kits/third-party/skills.lock`; do not edit them directly.

| Skill | Description |
|---|---|
| `find-skills` | Helps users discover and install agent skills when they ask questions like "how do I do X", "find a skill for X", "is there a skill that can...", or express interest in extending capabilities. This skill should be used when the user is looking for functionality that might exist as an installable skill. |
| `frontend-design` | Guidance for distinctive, intentional visual design when building new UI or reshaping an existing one. Helps with aesthetic direction, typography, and making choices that don't read as templated defaults. |
| `grilling` | Grill the user relentlessly about a plan, decision, or idea. Use when the user wants to stress-test their thinking, or uses any 'grill' trigger phrases. |
| `skill-creator` | Create new skills, modify and improve existing skills, and measure skill performance. Use when users want to create a skill from scratch, edit, or optimize an existing skill, run evals to test a skill, benchmark skill performance with variance analysis, or optimize a skill's description for better triggering accuracy. |
