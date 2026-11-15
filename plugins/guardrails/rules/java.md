---
description: Always/never constraints for Java and Maven files; build, Java 25, JdbcClient, ArchUnit and Testcontainers detail is in the sdd-implement java references.
trigger: glob
globs:
  - "**/*.java"
  - "**/pom.xml"
paths:
  - "**/*.java"
  - "**/pom.xml"
---

Always/never for `*.java` and `pom.xml`; names, functions and errors: rule `code.md`; tests: rule `tests.md`. Detail: skill `sdd-implement`, reference `java/README.md` (build and modules, Java 25 facts, JdbcClient and Flyway, ArchUnit, Testcontainers).

- Always: build with the Maven wrapper `./mvnw` at the LTS the repo fixes (`pom.xml`, `.java-version`, toolchains); never global `mvn`, Gradle or a PATH JDK.
- Always: packages by layer: `domain` (entities, value objects, domain services and errors), `application` (use cases and ports, depends inward on domain), `adapter-*`/`infrastructure` (HTTP, persistence, messaging), `bootstrap` (framework configuration and wiring).
- Never: a framework import (`org.springframework`, `jakarta.persistence`, `java.sql`) in `domain/`; the ArchUnit gate fails it.
- Never: `Instant.now()`, `LocalDate.now()`, `new Random()` or `Math.random()` in `domain/`; inject `java.time.Clock` and `java.util.random.RandomGenerator` ports.
- Always: constructor injection in a `final` class with `private final` fields, never field `@Autowired`; Spring configuration through `@ConfigurationProperties`, Quarkus services in the matching CDI scope.
- Always: `record` for DTOs, `@ConfigurationProperties` and value carriers, and `sealed` hierarchies for a closed set of variants; a persistence entity never crosses the adapter boundary.
- Always: `Optional` only as a return type for an absent value, never a parameter or field type, and never `null` returned in its place.
- Always: `var` only when the initializer shows the type; a stream only when it reads clearer than the loop.
- Always: concise JavaDoc on public API stating its purpose or invariant.
- Always: a schema change is a new `V<n+1>__<slug>.sql` under `src/main/resources/db/migration/` (rule `migrations.md`); editing an applied migration is ask-first (`AGENTS.md` Boundaries).
- Always: the persistence style the repo `AGENTS.md` declares (`JdbcClient` with hand-written SQL, or JPA); never introduce the other one.
- Always: domain tests in pure JUnit 5 and AssertJ without `@SpringBootTest`; Mockito only at ports; a full Spring or Quarkus context only when the behavior needs framework wiring.
- Never: `@SuppressWarnings` to hide a warning; `unused` means delete the code, and `unchecked` sits only on the narrowest declaration with a comment naming why the type cannot be expressed.
- Never: catch `Exception`, `Throwable` or `RuntimeException` and go on silently; catch the narrowest type and keep the cause (`throw new X(..., e)`); a broad catch stays only where a failure must not stop a connection, loop or schedule, logged with the exception as the last argument.
- Always: SLF4J logging without credentials or personal data; an external failure becomes a specific domain or application error, never a generic `RuntimeException`.
- Never: `@Disabled` to go green, `ddl-auto=update`, or a secret in `application*.yml`.
- Always: before a PR, the build gate the repo `AGENTS.md` names green (`./mvnw spotless:check verify` when it names none), with the literal tail pasted as proof.
