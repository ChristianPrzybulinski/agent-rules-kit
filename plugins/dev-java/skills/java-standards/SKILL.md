---
name: java-standards
description: Java 25, Spring/Quarkus and JUnit standards. Use when editing *.java, pom.xml, Spring/Quarkus code or JUnit tests. Not for general test policy (skill testing).
triggers:
  - user
  - model
allowed-tools:
  - read
  - grep
  - glob
  - exec
  - edit
---

# Java Standards

Names and functions: read skill `clean-code`. Test gates and coverage: read skill `testing`.

Read `references/build-and-dependencies.md` for Maven/module gates and `references/java-25-lts.md` for verified Java 25 and Spring Boot 4.1 facts.
Persisting without JPA: read `references/jdbcclient-flyway.md`. Architecture gate: read `references/archunit-rules.md`.
Integration tests on a real database or broker: read `references/testcontainers.md` (Spring Boot container beans, reuse, sandbox caching).

## 1. Confirm the baseline

Inspect `pom.xml`, `.java-version`, Maven wrapper and toolchains. This kit uses fixed Java 25 LTS and Maven; do not silently adopt the PATH JDK or Gradle.

## 2. Preserve package boundaries

- `domain`: entities, value objects, domain services and errors; no framework imports.
- `application`: use cases and ports; depends inward on domain.
- `adapter-*`/`infrastructure`: HTTP, persistence, messaging and external implementations.
- `bootstrap`: framework configuration and wiring.

## 3. Apply Java language choices

- Use `record` for immutable DTO/value carriers and `sealed` hierarchies when the variant set is closed.
- Use `Optional` for an absent return, never for fields/parameters and never return `null` in its place.
- Use `var` only when the initializer makes the type obvious; use streams only when clearer than the loop.
- Document public APIs with concise JavaDoc that states purpose or invariant.

## 4. Apply framework boundaries

- Spring/Quarkus use constructor injection; no field injection.
- Spring configuration uses `@ConfigurationProperties`; Quarkus services use the appropriate CDI scope.
- Persistence lives in the outbound adapter; with JPA the entity never leaves it, without JPA follow `references/jdbcclient-flyway.md`.

## 5. Write JUnit tests

Use JUnit 5 and AssertJ; use Mockito only at ports. Domain tests run without Spring/Quarkus context; load a full context only when the behavior requires framework wiring. General coverage/mutation policy belongs to `testing`.

## 6. Verify

Run the Maven wrapper with the project modules/gates from the build reference. Use SLF4J without sensitive data and translate external errors rather than throwing generic `RuntimeException`.

Done when: Java 25/Maven are fixed, framework dependencies stay outside domain/application, JUnit scope matches the behavior, and the relevant Maven gate passes.
