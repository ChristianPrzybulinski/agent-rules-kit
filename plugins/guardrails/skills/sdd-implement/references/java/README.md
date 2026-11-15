# Java references

Facts and procedures for Java 25 with Maven, Spring Boot or Quarkus and JUnit 5. The always/never for `*.java` and `pom.xml` is rule `java.md`; layers and ports are skill `sdd-plan`, reference `architecture.md`.

## How to use

1. Before changing `pom.xml`, a module or the build gate, read `build-and-dependencies.md` (module gates, offline flags).
2. Before relying on a Java 25 or Spring Boot 4.1 feature, check it in `java-25-lts.md`.
3. Persisting without JPA: `jdbcclient-flyway.md`. Architecture gate: `archunit-rules.md`.
4. An integration test on a real database or broker: `testcontainers.md` (Spring Boot container beans, reuse, sandbox caching).
5. Verify with the build gate the repo `AGENTS.md` names (`./mvnw spotless:check verify` when it names none) and paste the literal tail.

## Contents

| File | Scope |
|---|---|
| [`build-and-dependencies.md`](build-and-dependencies.md) | Maven wrapper, modules, gates and offline runs |
| [`java-25-lts.md`](java-25-lts.md) | verified Java 25 and Spring Boot 4.1 facts |
| [`jdbcclient-flyway.md`](jdbcclient-flyway.md) | `JdbcClient` with hand-written SQL and Flyway migrations |
| [`archunit-rules.md`](archunit-rules.md) | the ArchUnit layer and import rules |
| [`testcontainers.md`](testcontainers.md) | Testcontainers with Spring Boot, reuse and caching |
