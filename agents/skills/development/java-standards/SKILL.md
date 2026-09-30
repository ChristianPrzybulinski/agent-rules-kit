---
name: java-standards
version: "2.0"
description: Applies modern Java standards — style (`var`, `Optional`, `record`, `sealed`), Clean Architecture packages, Spring/Quarkus, JUnit 5 tests. Use on `*.java` or `pom.xml`. Do not use for build/module/plugin gates detail (`references/build-and-dependencies.md`) or the general test policy (skill testing).
triggers:
  - user
  - model
allowed-tools:
  - read
  - grep
  - glob
  - exec
---

# Java Expert

Build, multi-module structure and quality plugins: `references/build-and-dependencies.md`.

## When working with Java

1. Check the baseline (`pom.xml`, `build.gradle`, `.java-version`): fixed Java LTS, Maven wrapper — detail in `references/build-and-dependencies.md`.
2. Respect the package structure (Clean Architecture):

```text
com.example.project
├── domain          # Entities, value objects, domain services, exceptions
├── application     # Use cases, ports (input/output interfaces)
├── infrastructure  # Port implementations: DB, HTTP, messaging
└── adapter         # Controllers, presenters, CLI, web
```

`domain`/`application` must not depend on external frameworks.

3. Language: `var` when the type is obvious; `Optional` for possibly-absent values (never return `null`); `Stream`/`Collectors` over imperative loops when functional is clearer; `record` for DTOs/immutables; `sealed` + pattern matching to model the domain.
4. Frameworks: Spring Boot — constructor injection (never field `@Autowired`), `@ConfigurationProperties` for config; Quarkus — constructor injection + `@ApplicationScoped`; JPA/persistence entities stay in infrastructure — domain entities separate when needed.
5. Tests: JUnit 5 + AssertJ/Mockito, `shouldCalculateTotalWhenAddingItem` naming; domain units without the Spring context; `@SpringBootTest` only when needed.
6. Dependencies: no new library without justification — check `pom.xml`/`build.gradle`, prefer the standard ecosystem (SLF4J, Jackson), validate compatibility with the project's Java.
7. Document public APIs with concise JavaDoc.

## Standard checks

- Names in English, per project convention.
- Avoid logic in controllers; delegate to use cases/services.
- Logging: SLF4J; never log sensitive data.
- Exceptions: specific domain exceptions, not generic `RuntimeException`; never swallow one silently.
