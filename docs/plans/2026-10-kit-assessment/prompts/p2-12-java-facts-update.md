# P2-12 — Update Java and Spring facts (Java 25, Spring Boot 4.1.x)

Phase: 2 · Repos: kit (agent-rules-kit) · Branch to create: fix/p2-12-java-spring-facts from main · Depends on: P2-01 · Effort: ~2 h

## Goal

Bring every Java and Spring statement in the kit to the line the one real consumer builds on: Java 25 LTS and Spring Boot 4.1.x. The project template stops prescribing Java 21, Boot 3.x, JPA and RFC 7807 and instead fixes Java 25 + Boot [4.1.x] and declares persistence (JdbcClient + Flyway without JPA, or JPA) and the error format (RFC 9457 ProblemDetail, or a project error catalog) as choices the project fills in, keeping the condition-to-action style. `pom-parent.xml` imports the 4.1.1 BOM with plugin versions taken from a working Boot 4.1.1 build. The `kind: fact` reference carries the dated Boot facts with sources. Measurable result: `grep -rn '3\.5\.16\|Spring Boot \[3\|Java \[21\]\|RFC 7807' plugins platforms docs --exclude-dir=plans` prints nothing (3 lines today: `pom-parent.xml:19`, template lines 7 and 38), `grep -c 'spring-boot.version>4.1.1<' platforms/kits/java-maven/pom-parent.xml` prints `1`, and all four kit gates stay green.

## Why

- assessment §4.4, "Outdated Java template": `project-agents-java-spring.md` says "Java [21], Spring Boot [3.x]", JPA and RFC 7807; the project uses Java 25, Boot 4.1, JdbcClient without JPA and its own error catalog; the kit's `pom-parent.xml` pins Boot 3.5.16, a line that left OSS support on 2026-06-30.
- assessment §6 item G1: update the template to Java 25 + Boot 4.x and `pom-parent.xml` to the current BOM (the GA line is 4.1.1). G2 (JdbcClient/Flyway and ArchUnit references) is P2-13, G3 (Testcontainers, offline Maven) is P2-14.
- assessment §9.2, Java row, verified 2026-10-06: Java 25 LTS GA 2025-09-16; Spring Boot GA 4.1.1 (2026-08-20); 3.5.x out of OSS support since 2026-06-30; Boot 4.1.x supports Java 17 to 27 (sources: oracle.com, spring.io, Maven Central).
- `platforms/kits/java-maven/pom-parent.xml:19` pins `3.5.16` with a "verified 2026-09-29" comment; stratics-docs `docs/spec/decisions/DTEC-009-spring-boot-4-1.md:27` decides "The agent-rules-kit `pom-parent.xml` is updated to the same line so new projects do not start on an unsupported version", and `:45` records 4.1.1 as the latest 4.1.x GA on Maven Central (2026-10-04; `4.2.0-M2` is a milestone), resolving `spring-core 7.0.9`, with `spring-boot-starter-parent:4.1.1` defaulting `java.version` to 17.
- stratics-server `pom.xml:10` (`4.1.1`), `:19-21` (release 25, toolchain `[25,26)`), `:111` jacoco `0.8.15`, `:121` pitest `1.30.0`, `:171` spotless `3.10.2`, `:181` google-java-format `1.30.0`, `:246` pitest-junit5 `1.2.3`, `:274` dependency-check `13.0.0`: a build that passes `./mvnw spotless:check verify` on JDK 25 (DTEC-009:45). These are the plugin versions to trust.
- stratics-server `AGENTS.md:8-9` had to override the template by hand ("no JPA/Hibernate (DTEC-005)", "errors are the FEAT-006 protocol catalog, not RFC 7807"): the template must offer both as declared choices instead of a default the project has to contradict.
- `platforms/kits/github/workflows/ci-java.yml:14-15` and `:40-41` already run `distribution: temurin`, `java-version: '25'`: verify only, no edit expected.

## Current state

All paths are in the kit repo (v10.1.0) unless prefixed `stratics-server/` or `stratics-docs/`. `wc -l`: template 72, `java-25-lts.md` 31, `build-and-dependencies.md` 47, `SKILL.md` 53. P2-01 must be merged first: it rewrites `java-25-lts.md:2` (description) and `:13` (project pins instead of "installed on this machine"); build on that version and keep its two lines.

```
plugins/dev-java/templates/project-agents-java-spring.md:7:- Java [21] LTS, Spring Boot [3.x]. Build via wrapper: `./mvnw` (or `./gradlew`). Never global `mvn`.
plugins/dev-java/templates/project-agents-java-spring.md:9:- Database: [PostgreSQL]; Flyway migrations in `src/main/resources/db/migration/V*.sql`.
plugins/dev-java/templates/project-agents-java-spring.md:15:├── domain/         # entities, value objects, domain exceptions — no Spring/JPA
plugins/dev-java/templates/project-agents-java-spring.md:17:├── adapter/        # in: controllers, DTOs, mappers | out: JPA repositories, HTTP clients
plugins/dev-java/templates/project-agents-java-spring.md:36:- Expose an endpoint → `record` DTO in/out; a JPA entity never leaves the adapter.
plugins/dev-java/templates/project-agents-java-spring.md:38:- Business error → specific domain exception in `domain/`; `@ControllerAdvice` converts to RFC 7807 (`ProblemDetail`).
plugins/dev-java/templates/project-agents-java-spring.md:39:- Filtered query → `Specification` or named query method; avoid string JPQL when a typed alternative exists.
plugins/dev-java/templates/project-agents-java-spring.md:67:- Ask first: change `pom.xml`/`build.gradle`; edit an already-applied migration; change Spring auto-config; change a public API contract.
plugins/dev-java/templates/project-agents-java-spring.md:68:- Never: `@Disabled` to go green; `.env` or credentials in the repo; `ddl-auto=update` in production.
platforms/kits/java-maven/pom-parent.xml:18:    <!-- Versions verified on Maven Central on 2026-09-29 -->
platforms/kits/java-maven/pom-parent.xml:19:    <spring-boot.version>3.5.16</spring-boot.version>
platforms/kits/java-maven/pom-parent.xml:20:    <spotless.version>3.10.3</spotless.version>
platforms/kits/java-maven/pom-parent.xml:21:    <google-java-format.version>1.36.1</google-java-format.version>
platforms/kits/java-maven/pom-parent.xml:22:    <jacoco.version>0.8.15</jacoco.version>
platforms/kits/java-maven/pom-parent.xml:23:    <pitest.version>1.30.0</pitest.version>
platforms/kits/java-maven/pom-parent.xml:24:    <pitest-junit5.version>1.2.3</pitest-junit5.version>
platforms/kits/java-maven/pom-parent.xml:25:    <dependency-check.version>13.0.0</dependency-check.version>
platforms/kits/java-maven/pom-parent.xml:28:    <flyway.version>13.8.1</flyway.version>
platforms/kits/java-maven/pom-parent.xml:37:  <dependencyManagement>
platforms/kits/java-maven/README.md:3:Parent POM with the kit's quality gates. Versions verified on Maven Central on 2026-09-29.
plugins/dev-java/skills/java-standards/references/java-25-lts.md:1:---
plugins/dev-java/skills/java-standards/references/java-25-lts.md:3:kind: fact
plugins/dev-java/skills/java-standards/references/java-25-lts.md:4:verified: "2026-09-29"
plugins/dev-java/skills/java-standards/references/java-25-lts.md:6:  - https://openjdk.org/projects/jdk/25/
plugins/dev-java/skills/java-standards/references/java-25-lts.md:31:Canonical JEP-per-release reference: https://openjdk.org/projects/jdk/25/
plugins/dev-java/skills/java-standards/references/build-and-dependencies.md:13:- Framework BOM (`spring-boot-dependencies`) instead of loose versions.
plugins/dev-java/skills/java-standards/references/build-and-dependencies.md:24:├── adapter-out-jpa/        # repositories, JPA entities, Flyway
plugins/dev-java/skills/java-standards/SKILL.md:19:Read `references/build-and-dependencies.md` for Maven/module gates and `references/java-25-lts.md` for verified Java 25 facts.
plugins/dev-java/skills/java-standards/SKILL.md:43:- Persistence/JPA entities stay in the outer adapter when the domain model carries behavior.
platforms/kits/github/workflows/ci-java.yml:14:          distribution: temurin
platforms/kits/github/workflows/ci-java.yml:15:          java-version: '25'
stratics-server/pom.xml:23:        <!-- Overrides the Tomcat 11.0.24 that Spring Boot 4.1.1 manages: dependency-check
stratics-server/pom.xml:28:        <tomcat.version>11.0.26</tomcat.version>
CHANGELOG.md:5:## [Unreleased]
CHANGELOG.md:11:### Changed
```

Validation that applies: `platforms/ci/schemas/reference.schema.json` (description at most 160 chars; `kind: fact` requires `verified` `YYYY-MM-DD` and `sources` with `https://` URLs); `check_kit.py:27` caps a reference at 60 lines; `check_kit.py:636` requires `SKILL.md` to name each reference; `check_kit.py:832` resolves backtick paths ending in `.md|.sh|.json|.yml|.yaml` inside templates, skills and `platforms/**/*.md`, so write placeholder decision-record paths in square brackets without backticks (as `p1-04` does) and never put a not-yet-existing `references/*.md` (P2-13's files) in backticks. No index change: `plugins/dev-java/INDEX.md:14` already lists the template, `platforms/kits/java-maven/README.md` already names every file in its folder, and no file is created or deleted.

## Change

1. Edit `plugins/dev-java/templates/project-agents-java-spring.md` (kit). Replace line 7 with (Gradle leaves: `build-and-dependencies.md:10` says "Gradle is not an option in this kit"):
   ```markdown
   - Java 25 LTS (`maven.compiler.release=25`, the kit's fixed LTS), Spring Boot [4.1.x] (never 3.5.x: out of OSS support since 2026-06-30). Build via the Maven wrapper: `./mvnw`. Never global `mvn`, never Gradle.
   ```
   After line 9 insert two bullets (declared choices, same bracket convention as the rest of the file):
   ```markdown
   - Persistence, declared choice: [JdbcClient + hand-written SQL + Flyway, no JPA/Hibernate | Spring Data JPA + Flyway]. Decision record: [docs/spec/decisions/DTEC-nnn-*.md | docs/adr/nnnn-*.md]. Delete the option not chosen and every line below tagged with the other option.
   - Errors, declared choice: [RFC 9457 `ProblemDetail` via `@ControllerAdvice` | project error catalog `{code, message, details?}` mapped in the inbound adapter]. Delete the option not chosen.
   ```
   Replace the comment on line 15 with `# entities, value objects, domain exceptions; no Spring, JDBC or JPA imports` and on line 17 with `# in: controllers or WS handlers, DTOs, mappers | out: repositories (JdbcClient or JPA), HTTP clients`. Replace lines 36, 38 and 39 with:
   ```markdown
   - Expose an endpoint → `record` DTO in/out; a persistence entity or row mapping never leaves the adapter.
   - Business error → specific domain exception in `domain/`; the inbound adapter converts it to the declared error format (RFC 9457 `ProblemDetail` or the catalog `{code, message, details?}`); never a generic 500 and never a stack trace in the body.
   - [JdbcClient] Query → repository port in `application/`, `JdbcClient` adapter with named parameters and an explicit `RowMapper`; never SQL built by string concatenation.
   - [JPA] Filtered query → `Specification` or named query method; avoid string JPQL when a typed alternative exists.
   ```
   Replace line 67 so it starts `- Ask first: change `pom.xml`; edit an already-applied migration; ...` (drop `/`build.gradle``) and line 68 with:
   ```markdown
   - Never: `@Disabled` to go green; `.env` or credentials in the repo; [JPA] `ddl-auto=update` outside tests; [JdbcClient] JPA annotations or `EntityManager` anywhere.
   ```
   Every other line stays as it is (title, `## Commands`, the `CreateOrder` example, `## More`).
2. Edit `platforms/kits/java-maven/pom-parent.xml` (kit). Replace lines 18-19 with:
   ```xml
       <!-- Versions verified on Maven Central on <YYYY-MM-DD>; the Boot BOM, JaCoCo, PIT, Spotless and
            dependency-check versions match a working Boot 4.1.1 build (stratics-server, 2026-10-05).
            A property marked "verify" could not be checked against Maven Central when it was written. -->
       <spring-boot.version>4.1.1</spring-boot.version>
   ```
   Keep `jacoco.version` 0.8.15, `pitest.version` 1.30.0, `pitest-junit5.version` 1.2.3 and `dependency-check.version` 13.0.0 (identical in the working build). For `spotless.version` (kit 3.10.3, working build 3.10.2) and `google-java-format.version` (kit 1.36.1, working build 1.30.0): keep the kit value only if you see it on https://central.sonatype.com (search `spotless-maven-plugin`, `google-java-format`); otherwise set the working-build value. For `flyway.version` (13.8.1): the Flyway plugin must match the `flyway-core` the 4.1.1 BOM manages; read it with `./mvnw -q help:evaluate -Dexpression=flyway.version -DforceStdout` in any project whose parent is `spring-boot-starter-parent:4.1.1` and set that value; if you cannot run it, keep 13.8.1 and append ` <!-- verify -->` on that line. Do the same check for `surefire.version`, `failsafe.version`, `enforcer.version` and `versions.version` against the expressions `maven-surefire-plugin.version`, `maven-failsafe-plugin.version`, `maven-enforcer-plugin.version`, `versions-maven-plugin.version`; keep the current pin plus ` <!-- verify -->` when the expression prints nothing. Insert above line 37 (`<dependencyManagement>`) this comment, grounded in stratics-server `pom.xml:23-28`:
   ```xml
     <!-- Boot 4.1.1 manages tomcat-embed-core 11.0.24, which fails the dependency-check gate (CVSS >= 7, nine
          CVE-2026-* findings). A project importing this BOM overrides Tomcat with explicit tomcat-embed-* entries
          placed BEFORE the import below; a tomcat.version property only works under spring-boot-starter-parent.
          Verify against the Boot 4.1.x release notes whether a newer patch already manages >= 11.0.26. -->
   ```
   Nothing else in the POM changes (enforcer `[25,26)`, profiles, plugin bindings).
3. Edit `platforms/kits/java-maven/README.md:3` (kit) to: `Parent POM with the kit's quality gates on the Spring Boot 4.1.x BOM (3.5.x left OSS support on 2026-06-30). Versions verified on Maven Central on <YYYY-MM-DD>; properties marked "verify" in the POM were not.` Add after line 19 a bullet under `## Gates`: `- **Tomcat override**: Boot 4.1.1 manages Tomcat 11.0.24, which fails dependency-check; see the comment above <dependencyManagement> in the parent POM.`
4. Edit `plugins/dev-java/skills/java-standards/references/java-25-lts.md` (kit, on top of P2-01). Set line 2 to:
   ```yaml
   description: Java 25 LTS and Spring Boot 4.1.x facts (GA dates, support windows, Java range, project pins, Temurin CI). Load when configuring a Java project, pom or CI.
   ```
   (155 chars.) Set `verified: "2026-10-06"` (the assessment §9.2 fact-check date), or today's date if you re-open every URL in `sources`. Add two sources after line 6: `https://spring.io/projects/spring-boot#support` and `https://docs.spring.io/spring-boot/system-requirements.html`. Rename the H1 to `# Java 25 (LTS) and Spring Boot 4.1 — facts` and append after line 31:
   ```markdown

   ## Spring Boot baseline

   - GA line: **4.1.x**; 4.1.1 released 2026-08-20 and the latest 4.1.x GA on Maven Central (verify against https://spring.io/projects/spring-boot#support before bumping). 4.0.x OSS support ends 2026-12-31; 3.5.x left OSS support on 2026-06-30 (3.5.16 was the last OSS patch). Never start a project on 3.5.x or 4.0.x.
   - Boot 4.1.x runs on Java 17 to 27, so Java 25 is inside the window; `spring-boot-starter-parent:4.1.1` defaults `java.version` to 17, so `<maven.compiler.release>25</maven.compiler.release>` is required (verify the upper bound against the system-requirements page before relying on it).
   - Kit pin: the parent POM in `platforms/kits/java-maven/` imports `spring-boot-dependencies:4.1.1`; a project built on `spring-boot-starter-parent` uses the same version. Boot 4 ships Spring Framework 7 (4.1.1 resolves `spring-core 7.0.9`) and Jackson 3 (`tools.jackson`): check artifact names before copying Boot 3 snippets.
   ```
   The file ends at 39 lines (31 after P2-01, plus 2 sources and the 6-line section; limit 60).
5. Edit `plugins/dev-java/skills/java-standards/references/build-and-dependencies.md` (kit). Line 13 becomes `- Framework BOM (`spring-boot-dependencies`, the 4.1.x line pinned in the parent POM; never 3.5.x, out of OSS support) instead of loose versions.` Line 24 becomes `├── adapter-out-persistence/ # repositories (JdbcClient or JPA, the declared choice), Flyway`. Nothing else.
6. Edit `plugins/dev-java/skills/java-standards/SKILL.md` (kit). Line 19: replace `for verified Java 25 facts` with `for verified Java 25 and Spring Boot 4.1 facts`. Line 43 becomes `- Persistence stays in the outer adapter (JPA entities or JdbcClient row mappings, the project's declared choice); the domain model carries behavior and no framework annotations.` The file stays at 53 lines; the `description:` line does not change.
7. `platforms/kits/github/workflows/ci-java.yml` (kit): confirm both jobs already use `distribution: temurin` and `java-version: '25'` (lines 14-15 and 40-41); make no edit. If `actions/setup-java` offers no Temurin 25 build at execution time, report it as unverified rather than changing the file.
8. Edit `CHANGELOG.md` (kit): add the bullet from Report back under `## [Unreleased]` / `### Changed` (line 11 today), with the before/after grep counts and the version-check commands as proof.
9. Do not touch `VERSION`, any path or manifest, `platforms/kits/java-maven/.java-version` (already `25`), `toolchains.xml.example` (P2-01), `dependency-check-suppressions.xml`, `plugins/dev-java/rules/java.md` or the Docker kit.

## Out of scope

- P2-01: removing "installed on this machine" from `java-25-lts.md:13` and the Homebrew path in `toolchains.xml.example`; this task starts after it is merged.
- P2-13: new references `jdbcclient-flyway.md` and `archunit-rules.md` and their `SKILL.md` links; this task only names JdbcClient as a declared choice in the template.
- P2-14: Testcontainers, `@ServiceConnection`, offline Maven, `-Pfast` guidance.
- P2-15 and stratics-server: `AGENTS.md`, `pom.xml` and the Tomcat override there; stratics-docs DTEC-009 is already closed for the server side and is NOT edited here.
- P1-01 freezes the 10.x layout: no file moves, no rename of the template (it keeps its `project-` prefix).
- The template's `## More` pointers (`docs/architecture.md`, `docs/adr/`): no owner in this plan (same note as `p1-04`); leave line 72 as is.

## Acceptance criteria

- [ ] `grep -rn '3\.5\.16\|Spring Boot \[3\|Java \[21\]\|RFC 7807\|7807' plugins platforms docs README.md --exclude-dir=plans` prints nothing (exit 1). Today it prints 3 lines.
- [ ] `grep -c 'spring-boot.version>4.1.1<' platforms/kits/java-maven/pom-parent.xml` prints `1`; `grep -c 'manages tomcat-embed-core' platforms/kits/java-maven/pom-parent.xml` prints `1` (the comment); `grep -c '2026-09-29' platforms/kits/java-maven/pom-parent.xml platforms/kits/java-maven/README.md` prints `0` for both.
- [ ] `xmllint --noout platforms/kits/java-maven/pom-parent.xml` exits 0.
- [ ] With network and JDK 25: `mvn -B -ntp -f platforms/kits/java-maven/pom-parent.xml validate` exits 0 (resolves `spring-boot-dependencies:4.1.1`, runs the enforcer). Without network: report unverified.
- [ ] `grep -c 'declared choice' plugins/dev-java/templates/project-agents-java-spring.md` prints `2`; `grep -c '9457' ...` prints `2`; `grep -c 'JdbcClient' ...` prints `4` or more; `grep -c 'gradle' ...` prints `0`.
- [ ] `grep -c 'Spring Boot baseline' plugins/dev-java/skills/java-standards/references/java-25-lts.md` prints `1`; `grep -c 'spring.io' ...` prints `3` or more; line 2 of the file is 160 characters or fewer after `description: ` (`awk 'NR==2{print length($0)-13}'`); `verified:` is `2026-10-06` or later.
- [ ] `wc -l` on `java-25-lts.md` and `build-and-dependencies.md` prints 60 or fewer each (today 31, 47); `wc -l plugins/dev-java/skills/java-standards/SKILL.md` prints `53`.
- [ ] `grep -c "java-version: '25'" platforms/kits/github/workflows/ci-java.yml` prints `2` and `git diff --stat main -- platforms/kits/github` prints nothing.
- [ ] `platforms/tools/check.sh` exits 0; `platforms/tools/smoke.sh` exits 0; `python3 -B -m unittest discover -s platforms/ci/validations -p "test_*.py"` reports `OK`; `python3 platforms/ci/validations/check_kit.py --links` exits 0 (reference schema, 60-line cap, SKILL.md linkage, backtick paths, description budget unchanged at 6,803).
- [ ] `grep -n 'P2-12\|Spring Boot 4.1' CHANGELOG.md` finds the new bullet between `## [Unreleased]` and `## [10.1.0]`.
- [ ] `git diff --stat main` lists only: the template, `pom-parent.xml`, `platforms/kits/java-maven/README.md`, `java-25-lts.md`, `build-and-dependencies.md`, `plugins/dev-java/skills/java-standards/SKILL.md`, `CHANGELOG.md`.

## Conventions

- Everything committed is in English.
- No layout or path change: the 10.x layout is frozen; `plugins/`, `platforms/`, `docs/`, manifests and install destinations keep their paths. The template keeps a name matching `^(spec|doc|project|kit)-[a-z0-9-]+\.md$`.
- `VERSION` untouched (no release in this task).
- `CHANGELOG.md` gets a `## [Unreleased]` entry written with evidence (what, why, proof).
- `INDEX.md` or `README.md` of every touched folder lists every entry by name: no entry is added or removed, so `plugins/dev-java/INDEX.md` and `platforms/kits/INDEX.md` are not edited; `platforms/kits/java-maven/README.md` is edited only in its text.
- References stay at 60 lines or fewer with frontmatter; `kind: fact` needs `verified` + `sources`; `kind: detail` (`build-and-dependencies.md`) needs neither; description at most 160 chars; the owning `SKILL.md` names each reference file.
- `SKILL.md` at 80 lines or fewer; skill descriptions are not touched, so the 7,200-char budget (6,803 today) does not move.
- Gates when the kit is touched: `platforms/tools/check.sh`; `platforms/tools/smoke.sh`; `python3 -B -m unittest discover -s platforms/ci/validations -p "test_*.py"`; `python3 platforms/ci/validations/check_kit.py --links`.
- Conventional Commits with Refs, for example `fix(dev-java): Java 25 + Spring Boot 4.1.x facts, persistence and error format as declared choices` with body `Refs: P2-12, assessment §4.4, §6 G1, §9.2`.
- PR body = What / Why / How I tested (literal output of the four gates, the acceptance greps, `xmllint`, and the `mvn validate` or the version-check commands) / Refs.
- Nothing here is Claude-specific; Devin or Claude Code can execute it with read, grep, edit and shell. Maven Central and spring.io lookups need network; without it, follow the "verify" fallbacks in Change steps 2 and 4.

## Report back

Final message format:

- done: each edited path with the line numbers changed; every command run (four gates, acceptance greps, `xmllint`, `mvn validate` or the `help:evaluate` checks) with its literal output; the final value of every `<*.version>` property and whether it was verified on Maven Central, taken from the working build, or left with `verify`.
- unverified: every fact or version you could not check (Maven Central or spring.io unreachable, `help:evaluate` not run, Temurin 25 availability), with the fallback you applied.
- next step: P2-13 (JdbcClient/Flyway and ArchUnit references, which will link from the same `SKILL.md`), P2-14 (Testcontainers and offline Maven), P2-15 (apply the regenerated template to stratics-server); the `docs/adr/` pointer in the template still has no owner.
- Proposed CHANGELOG line (under `### Changed`):
  `- Java and Spring facts updated to Java 25 LTS + Spring Boot 4.1.x: the project-agents-java-spring template fixes Java 25 and Boot [4.1.x] and declares persistence (JdbcClient + Flyway without JPA, or JPA) and the error format (RFC 9457 ProblemDetail, or a project error catalog) as project choices; pom-parent.xml imports the 4.1.1 BOM (3.5.x left OSS support on 2026-06-30) with plugin versions from a working Boot 4.1.1 build and a Tomcat-override note for the dependency-check gate; java-25-lts.md carries the dated Boot facts with spring.io sources; ci-java.yml already ran Temurin 25. Evidence: grep for '3.5.16|Spring Boot [3|Java [21]|RFC 7807' over plugins, platforms and docs went from 3 lines to 0 (P2-12, assessment §4.4, §6 G1, §9.2; stratics-docs DTEC-009).`
