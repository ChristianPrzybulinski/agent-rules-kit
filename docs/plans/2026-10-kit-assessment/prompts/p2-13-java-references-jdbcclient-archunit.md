# P2-13 — Java references: JdbcClient plus Flyway pattern and ArchUnit rules

Phase: 2 · Repos: kit (agent-rules-kit) · Branch to create: docs/p2-13-java-references-jdbcclient-archunit from main · Depends on: P2-12 · Effort: ~2 h

## Goal

Add two `kind: detail` references to the `java-standards` skill in the kit: `references/jdbcclient-flyway.md` (the no-JPA persistence pattern: `JdbcClient` repository with an explicit `RowMapper`, named parameters, the transaction boundary in the application service, idempotency through a command receipt row written in the same transaction, injected `Clock` and `RandomGenerator`, forward-only Flyway `V<n>__slug.sql`, Testcontainers for the integration test) and `references/archunit-rules.md` (the rule set of the Stratics server `ArchitectureTest` with placeholder package names, plus the Spring Modulith `ApplicationModules.verify()` alternative). Link both from `SKILL.md`. Measurable result: both files exist at 60 lines or fewer with valid frontmatter, `SKILL.md` names both file names and stays at 80 lines or fewer, no project-specific identifier (`br.com.pos`, `DTEC-`, `REQ-`, `FEAT-`) appears in `plugins/dev-java/`, and all four kit gates stay green.

## Why

- assessment §6 G2 (authoritative shape of this change): add `references/jdbcclient-flyway.md` (the no-JPA pattern the project adopted: `JdbcClient`, explicit mapping, injected `Clock`, idempotency through `command_receipts`) and `references/archunit-rules.md` with the `ArchitectureTest` rule set as a template.
- The skill today says nothing about how to persist without JPA. `plugins/dev-java/skills/java-standards/SKILL.md:43` reads "Persistence/JPA entities stay in the outer adapter when the domain model carries behavior." and `references/build-and-dependencies.md:24` names the module `adapter-out-jpa/ # repositories, JPA entities, Flyway`. The Stratics server forbids JPA outright: stratics-server `AGENTS.md:8` reads "Spring `JdbcClient` + hand-written SQL + Flyway" followed by "no JPA/Hibernate (DTEC-005)" and `AGENTS.md:64` lists "JPA annotations or `EntityManager` anywhere" under Never.
- The ArchUnit gate exists only as a one-word mention: `references/build-and-dependencies.md:28` reads "Inter-module dependency rule verified at build time (`maven-enforcer` `bannedDependencies` or ArchUnit in `domain`)." The working rule set lives in stratics-server `src/test/java/br/com/pos/ArchitectureTest.java` (285 lines, 4 gate tests plus 4 negative tests) and nowhere in the kit; every new Java project would rewrite it from scratch.
- The receipt pattern is proven in production code: stratics-server `src/main/java/br/com/pos/application/command/CommandExecutor.java:36-57` runs effects and `receipts.saveIfAbsent(...)` inside one `transactions.inTransaction(...)`, with `clock.instant()` as the only time source, and `src/main/resources/db/migration/V2__command_receipts.sql:16` makes `command_id` unique as the integrity backstop.
- Measured: `grep -rn 'JdbcClient\|RowMapper\|ArchUnit' plugins/dev-java/` finds 1 line (`build-and-dependencies.md:28`); `grep -rn 'Clock\|RandomGenerator' plugins/dev-java/` finds 0 lines. The kit gives no guidance on deterministic time or randomness in Java, although stratics-server `AGENTS.md:47` makes it a gate: "`Instant.now()`/`Math.random()` in `domain/` fail the ArchUnit gate."

## Current state

All kit paths are relative to the agent-rules-kit repo (v10.1.0, branch to create from `main`). The skill folder holds `SKILL.md` (53 lines) and `references/build-and-dependencies.md` (47 lines) and `references/java-25-lts.md` (31 lines). There is no `references/jdbcclient-flyway.md` and no `references/archunit-rules.md` (both are new files). The folder's index is `plugins/dev-java/INDEX.md`; it lists skills, rules and templates only, references are not listed there (skills folders are exempt), so it does not change.

`plugins/dev-java/skills/java-standards/SKILL.md:17-19`:

```
Names and functions: read skill `clean-code`. Test gates and coverage: read skill `testing`.

Read `references/build-and-dependencies.md` for Maven/module gates and `references/java-25-lts.md` for verified Java 25 facts.
```

`plugins/dev-java/skills/java-standards/SKILL.md:39-43`:

```
## 4. Apply framework boundaries

- Spring/Quarkus use constructor injection; no field injection.
- Spring configuration uses `@ConfigurationProperties`; Quarkus services use the appropriate CDI scope.
- Persistence/JPA entities stay in the outer adapter when the domain model carries behavior.
```

Validator facts (`platforms/ci/validations/check_kit.py:27` sets `REFERENCE_MAX_LINES = 60`; `:624-637` validates every `skills/*/references/*.md` against `platforms/ci/schemas/reference.schema.json` and fails when the file name is not found in the skill's `SKILL.md`; `:832` resolves every backticked `references/...md` path relative to the file that cites it). The schema requires `description` (max 160 chars) and `kind` (`fact` or `detail`); `verified` and `sources` are required only for `kind: fact`; no other key is allowed.

Source material to de-project (read-only, stratics-server repo, package `br.com.pos`):

- `src/main/resources/db/migration/V2__command_receipts.sql:7-20`: table `command_receipts` with `command_id uuid NOT NULL` (the idempotency key), `account_id`, `type text`, `payload_hash bytea` (SHA-256 of the validated payload), `result jsonb` (the answer replayed on repetition), `created_at timestamptz`, `UNIQUE (command_id)`, a CHECK on `type` format and a CHECK `octet_length(payload_hash) = 32`.
- `src/main/java/br/com/pos/adapters/outbound/persistence/JdbcCommandReceiptRepository.java:15-23` declares `private static final RowMapper<CommandReceipt> MAPPER = (rs, row) -> new CommandReceipt(rs.getObject("command_id", UUID.class), ...)`; `:33-38` is `jdbc.sql("SELECT ... WHERE account_id = ? AND command_id = ?").params(accountId, commandId).query(MAPPER).optional()`; `:43-55` is the `INSERT ... ON CONFLICT ON CONSTRAINT uq_command_receipts_command_id DO NOTHING` whose `.update() == 1` tells the caller whether the receipt was stored.
- `src/main/java/br/com/pos/adapters/outbound/persistence/SpringTransactionRunner.java:19-22`: `inTransaction(Supplier<T> work)` is `template.execute(status -> work.get())` on a `TransactionTemplate`; the port `TransactionRunner` lives in `application/command/`.
- `src/main/java/br/com/pos/adapters/outbound/persistence/Timestamps.java:13-20`: `Instant` to `OffsetDateTime` (UTC) on write and back on read.
- `src/main/java/br/com/pos/application/command/CommandExecutor.java:36-57` (quoted in Why): find receipt, compare `type` and `payloadHash` (mismatch throws), else run effects, `saveIfAbsent` with `clock.instant()`, and throw when the insert did not store a row (lost race) so the transaction rolls the effects back.
- `src/test/java/br/com/pos/adapters/outbound/persistence/CommandTransactionIT.java:28-35`: `@Testcontainers` class with `@Container static final PostgreSQLContainer POSTGRES = new PostgreSQLContainer("postgres:18")`; `:63-66` migrates with `Flyway.configure().dataSource(dataSource).load().migrate()` in `@BeforeAll`; wiring uses `JdbcClient.create(ds)` and `Clock.fixed(NOW, ZoneOffset.UTC)`.
- `src/test/java/br/com/pos/ArchitectureTest.java:45-52` (`importsOnlyJdkAndDomain`: domain classes `onlyDependOnClassesThat` reside in `java..`, `javax..` or the domain package), `:54-69` (`noFrameworkOrLegacyImports`: `resideOutsideOfPackages("org.springframework..", "com.fasterxml.jackson..", "tools.jackson..", "java.sql..", "javax.sql..", "jakarta.websocket..", "jakarta.servlet..", "org.postgresql..", ...)`), `:72-78` and `:97-116` (`noNondeterminism`: no call to `Math.random`, `System.currentTimeMillis/nanoTime`, any `java.time.*.now`, `ThreadLocalRandom`, `UUID.randomUUID`, `Clock.system*`, `SecureRandom.getInstance*`, and no `new Random()`), `:139-162` (`layeredArchitecture().consideringOnlyDependenciesInLayers()` with layers Domain, Application, Adapters, Infra, Content and `mayOnlyBeAccessedByLayers(...)` pointing inwards), `:175-215` (negative fixtures `Bad*` and `GoodPure` that prove each rule fires). `pom.xml:94-96` uses `com.tngtech.archunit:archunit-junit5:1.5.1`.

## Change

1. Create `plugins/dev-java/skills/java-standards/references/jdbcclient-flyway.md` (kit, new file, 60 lines or fewer including frontmatter). Frontmatter, verbatim:

```
---
description: JdbcClient persistence without JPA: explicit RowMapper, named parameters, transaction boundary, receipt-based idempotency, Flyway, Testcontainers.
kind: detail
---
```

   Body outline, in this order, each as a short section with one fenced Java or SQL snippet where the pattern is clearer as code than as prose (keep every snippet to 8 lines or fewer):
   - Module placement: repository port (interface) in `application`, `Jdbc*Repository` class in the outbound persistence adapter, package-private and `final`, constructor-injected `JdbcClient`.
   - Mapping: one `private static final RowMapper<T>` per row type; read typed columns (`rs.getObject("id", UUID.class)`, `rs.getObject("created_at", OffsetDateTime.class).toInstant()`); no reflection-based mapping; a `Timestamps`-style helper converts `Instant` to `OffsetDateTime` (UTC) on both sides.
   - Parameters: prefer named parameters (`:name` in SQL, `.param("name", value)`), positional `?` only for one-parameter statements; never concatenate values into SQL.
   - Transaction boundary: a `TransactionRunner` port (`<T> T inTransaction(Supplier<T>)`) in `application`, implemented in the adapter on `TransactionTemplate`; the application service, never the repository, opens the transaction; no external I/O inside it.
   - Idempotency: a receipt table (`command_id uuid UNIQUE`, `account_id`, `type`, `payload_hash bytea` with a length CHECK, `result jsonb`, `created_at timestamptz`); the service finds the receipt first and replays `result` when `type` and `payload_hash` match, throws when they differ, otherwise runs the effects and inserts the receipt with `ON CONFLICT ... DO NOTHING` in the same transaction; `update() != 1` means a lost race, so throw and let the transaction undo the effects. Retention: a sweep by `created_at`, never in the request path.
   - Time and randomness: `java.time.Clock` and `java.util.random.RandomGenerator` are constructor parameters of application and domain classes; production wiring supplies `Clock.systemUTC()` and a seeded or default generator in the configuration class only; tests pass `Clock.fixed(...)` and a seeded generator.
   - Flyway: `src/main/resources/db/migration/V<n>__<slug>.sql`, forward-only, one concern per file, integrity (CHECK, UNIQUE, FK) in the migration; never edit an applied migration (add `V<n+1>`), never `ddl-auto`, never `flyway:clean` outside a throwaway database.
   - Integration test: Testcontainers PostgreSQL, run Flyway against the container before the tests, `JdbcClient.create(dataSource)`, truncate between tests; class suffix `IT`. One line pointing to the `@ServiceConnection` and reuse guidance owned by P2-14 (write "see the Testcontainers reference" without naming a file that does not exist yet).

   Use `com.example.app` as the package placeholder; do not copy any `br.com.pos`, `DTEC-`, `REQ-`, `FEAT-` or `Stratics` identifier.

2. Create `plugins/dev-java/skills/java-standards/references/archunit-rules.md` (kit, new file, 60 lines or fewer). Frontmatter, verbatim:

```
---
description: ArchUnit rule set for a hexagonal Java service (domain purity, no nondeterminism, layers point inwards) and the Spring Modulith verify() alternative.
kind: detail
---
```

   Body outline:
   - Setup: `com.tngtech.archunit:archunit-junit5` test dependency (write "verify the current version on Maven Central before relying on it"); import with `new ClassFileImporter().withImportOption(ImportOption.Predefined.DO_NOT_INCLUDE_TESTS).importPackages("<root>")`; one plain JUnit test class, no Spring context.
   - Rule 1, domain depends only on the JDK and itself: `classes().that(resideInAPackage("<root>.domain..")).should().onlyDependOnClassesThat(resideInAPackage("java..").or(resideInAPackage("javax..")).or(resideInAPackage("<root>.domain..")))`.
   - Rule 2, no framework or infrastructure imports in domain (and application, if the project chooses): `resideOutsideOfPackages("org.springframework..", "com.fasterxml.jackson..", "tools.jackson..", "java.sql..", "javax.sql..", "jakarta.servlet..", "jakarta.websocket..", "org.postgresql..")`.
   - Rule 3, no nondeterminism: a `DescribedPredicate<JavaMethodCall>` that rejects `Math.random`, `System.currentTimeMillis`, `System.nanoTime`, any `java.time.*` `now`, `ThreadLocalRandom`, `UUID.randomUUID`, `Clock.system*`, `SecureRandom.getInstance*`, plus `callConstructorWhere` the target is assignable to `java.util.Random`; give the predicate body as one fenced snippet of at most 12 lines.
   - Rule 4, layers point inwards: `layeredArchitecture().consideringOnlyDependenciesInLayers()` with layers `Domain`, `Application`, `Adapters`, `Infra` and `whereLayer("Domain").mayOnlyBeAccessedByLayers("Application", "Adapters", "Infra")`, `whereLayer("Application").mayOnlyBeAccessedByLayers("Adapters", "Infra")`, `whereLayer("Adapters").mayOnlyBeAccessedByLayers("Infra")`, `whereLayer("Infra").mayNotBeAccessedByAnyLayer()`; `.allowEmptyShould(true)` on every rule so an empty module does not pass vacuously by accident but a not-yet-populated layer does not fail the build.
   - Negative fixtures: nested `static final class Bad*` violators plus one `GoodPure` class, and tests asserting `assertThatThrownBy(() -> rule.check(withFixtures)).isInstanceOf(AssertionError.class).hasMessageContaining("Bad...")`; state that a rule without a failing fixture is not a gate.
   - Alternative, Spring Modulith: `ApplicationModules.of(Application.class).verify()` in one test enforces module boundaries from the package layout (`spring-modulith-starter-test`); write "verify against https://docs.spring.io/spring-modulith/reference/ before relying on it" next to the artifact name. Use it when the project is one Spring Boot application split into modules by package; keep ArchUnit when the rules go beyond module dependencies (nondeterminism, banned packages).
   - Policy line: never `@Disabled` or delete an architecture test to make a build pass; fix the dependency or change the rule in the same PR with the reason.

3. Edit `plugins/dev-java/skills/java-standards/SKILL.md` (kit). Replace line 19 with the two lines below, verbatim, so the file names of both references appear (check_kit.py matches the file name as a substring):

```
Read `references/build-and-dependencies.md` for Maven/module gates and `references/java-25-lts.md` for verified Java 25 facts.
Persisting without JPA: read `references/jdbcclient-flyway.md`. Architecture gate: read `references/archunit-rules.md`.
```

   Then replace line 43 ("Persistence/JPA entities stay in the outer adapter when the domain model carries behavior.") with:

```
- Persistence lives in the outbound adapter; with JPA the entity never leaves it, without JPA follow `references/jdbcclient-flyway.md`.
```

   Do not change the frontmatter `description` (the skill description budget stays at its current total). The file stays at 54 lines or fewer.

4. Edit `CHANGELOG.md` (kit): add one bullet under `## [Unreleased]` / `### Added` stating what (the two references and the SKILL.md links), why (assessment §6 G2; the skill mentioned JPA only, while the Stratics server forbids JPA and keeps its ArchUnit rules outside the kit) and proof (the four gate commands and the two `wc -l` results).

No change to `plugins/dev-java/INDEX.md`, `plugin.json`, `VERSION`, `rules/java.md` or `templates/project-agents-java-spring.md`.

## Out of scope

- Java 25 and Spring Boot 4.1.x fact updates in `references/java-25-lts.md`, `templates/project-agents-java-spring.md` and `platforms/kits/java-maven/`: P2-12 (this prompt depends on it only so the template no longer says "JPA repositories" by default; if P2-12 is not merged yet, proceed and do not touch the template).
- Replacing `adapter-out-jpa/` in `references/build-and-dependencies.md:24` with a neutral name: P2-12.
- Testcontainers `@ServiceConnection`, containers as beans, `reuse`, `-Pfast` and offline Maven: P2-14 (the integration-test section here stops at "Testcontainers plus Flyway migrate before tests").
- Real constraints in `plugins/dev-java/rules/java.md` (JdbcClient without JPA, injected Clock/RNG, ArchUnit, migration never edited): P2-02.
- Removing "Installed on this machine" from `references/java-25-lts.md:13`: P2-01.
- Changing the stratics-server `ArchitectureTest.java` or any stratics-server file: no prompt; the server is read-only input here.

## Acceptance criteria

- [ ] `test -f plugins/dev-java/skills/java-standards/references/jdbcclient-flyway.md && test -f plugins/dev-java/skills/java-standards/references/archunit-rules.md` exits 0.
- [ ] `wc -l plugins/dev-java/skills/java-standards/references/jdbcclient-flyway.md plugins/dev-java/skills/java-standards/references/archunit-rules.md plugins/dev-java/skills/java-standards/SKILL.md` prints each reference at 60 or fewer and `SKILL.md` at 80 or fewer.
- [ ] `head -4 plugins/dev-java/skills/java-standards/references/jdbcclient-flyway.md` and the same for `archunit-rules.md` show `---`, `description:`, `kind: detail`, `---`; `grep -c '^verified:\|^sources:' <each file>` prints `0`.
- [ ] `grep -c 'jdbcclient-flyway.md' plugins/dev-java/skills/java-standards/SKILL.md` prints `2` and `grep -c 'archunit-rules.md' plugins/dev-java/skills/java-standards/SKILL.md` prints `1`.
- [ ] `grep -rn 'br\.com\.pos\|DTEC-\|REQ-\|FEAT-\|Stratics' plugins/dev-java/` prints nothing.
- [ ] `grep -c 'RowMapper' plugins/dev-java/skills/java-standards/references/jdbcclient-flyway.md` prints at least `1`; `grep -c 'ON CONFLICT' ...jdbcclient-flyway.md` prints at least `1`; `grep -c 'RandomGenerator' ...jdbcclient-flyway.md` prints at least `1`; `grep -c 'V<n>__' ...jdbcclient-flyway.md` prints at least `1`.
- [ ] `grep -c 'layeredArchitecture\|onlyDependOnClassesThat\|ApplicationModules' plugins/dev-java/skills/java-standards/references/archunit-rules.md` prints `3` or more; `grep -c 'randomUUID' ...archunit-rules.md` prints at least `1`.
- [ ] `grep -c 'JPA' plugins/dev-java/skills/java-standards/SKILL.md` prints `1` (the rewritten line 43 only).
- [ ] `git diff --stat main -- plugins/dev-java/INDEX.md VERSION plugins/dev-java/plugin.json` prints nothing.
- [ ] `grep -n 'jdbcclient-flyway\|archunit-rules' CHANGELOG.md` finds the new bullet under `## [Unreleased]`.
- [ ] Gates: `platforms/tools/check.sh` exits 0; `platforms/tools/smoke.sh` exits 0; `python3 -B -m unittest discover -s platforms/ci/validations -p "test_*.py"` prints `OK`; `python3 platforms/ci/validations/check_kit.py --links` exits 0 with no `not referenced in` and no `broken link` line.

## Conventions

- Everything committed is in English; ASCII punctuation in the new files.
- No layout or path change: the 10.x layout is frozen; the two files go under the existing `references/` folder of the existing skill.
- `VERSION` untouched; `CHANGELOG.md` gets a `## [Unreleased]` bullet with evidence (what, why, proof).
- `plugins/dev-java/INDEX.md` does not list references (skills folders are exempt) and does not change; the skill description is not edited, so the per-skill 40-160 chars rule and the 7,200-char total budget are unaffected.
- `SKILL.md` 80 lines or fewer; each reference 60 lines or fewer with frontmatter; `kind: detail` carries no `verified` or `sources` key (`platforms/ci/schemas/reference.schema.json` forbids extra keys).
- Every backticked `references/<file>.md` in `SKILL.md` must resolve relative to the skill folder (`check_kit.py --links`).
- Conventional Commits with Refs, for example `docs(dev-java): add JdbcClient/Flyway and ArchUnit references` with `Refs: assessment §6 G2, P2-13`.
- PR body = What / Why / How I tested (literal output of the four gate commands and the `wc -l` line) / Refs.
- Gates when the kit is touched: `platforms/tools/check.sh`; `platforms/tools/smoke.sh`; `python3 -B -m unittest discover -s platforms/ci/validations -p "test_*.py"`; `python3 platforms/ci/validations/check_kit.py --links`.

## Report back

Final message in three parts: done (the three edited or created kit paths, the branch name, and each gate command with its literal last line), unverified (anything not run, for example the Spring Modulith artifact name or the ArchUnit version if the network was unavailable), next step (P2-14 for `@ServiceConnection` and offline Maven; P2-02 for the path-scoped rule lines). Close with the proposed one-line CHANGELOG entry:

`- dev-java/java-standards: references/jdbcclient-flyway.md (JdbcClient without JPA, receipt-based idempotency, injected Clock/RandomGenerator, forward-only Flyway, Testcontainers) and references/archunit-rules.md (domain purity, no nondeterminism, inward layers, Spring Modulith alternative), linked from SKILL.md. Evidence: assessment §6 G2; the skill mentioned JPA only while the Stratics server forbids JPA and kept its ArchUnit rule set outside the kit.`
