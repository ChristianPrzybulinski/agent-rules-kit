---
description: Always/never constraints for Java and Maven files; procedures stay in skill java-standards.
trigger: glob
globs:
  - "**/*.java"
  - "**/pom.xml"
paths:
  - "**/*.java"
  - "**/pom.xml"
---

Always/never for `*.java` and `pom.xml`. Procedures: skill `java-standards` (names: `code-standards`; test gates: `testing`).

- Always: build with the Maven wrapper `./mvnw` at the LTS the repo fixes; never global `mvn`, Gradle or a PATH JDK.
- Never: a framework import (`org.springframework`, `jakarta.persistence`, `java.sql`) in `domain/`; the ArchUnit gate fails it.
- Never: `Instant.now()`, `LocalDate.now()`, `new Random()` or `Math.random()` in `domain/`; inject `java.time.Clock` and `java.util.random.RandomGenerator` ports.
- Always: constructor injection in a `final` class with `private final` fields; never field `@Autowired`.
- Always: `record` for DTOs, `@ConfigurationProperties` and value carriers; a persistence entity never crosses the adapter boundary.
- Always: `Optional` only as a return type, never a parameter or field type.
- Never: edit an applied Flyway migration; a schema change is a new `V<n+1>__<slug>.sql` under `src/main/resources/db/migration/`.
- Always: the persistence style the repo `AGENTS.md` declares (`JdbcClient` with hand-written SQL, or JPA); never introduce the other one.
- Always: domain tests in pure JUnit 5 and AssertJ without `@SpringBootTest`; Mockito only at ports.
- Never: `@SuppressWarnings` to hide a warning; `unused` means delete the code, and `unchecked` sits only on the narrowest declaration with a comment naming why the type cannot be expressed.
- Never: `@Disabled` to go green, `ddl-auto=update`, or a secret in `application*.yml`.
- Always: `./mvnw spotless:check verify` green before a PR, with the literal tail pasted as proof.
