---
description: Specific rules for modern Java development, Clean Code and Clean Architecture. Load for `*.java` code.
trigger: model_decision
---

# Java

## Style and language

- Use Java 17+ as baseline. Prefer `var` when the type is obvious.
- Use `Optional` for values that may be absent; avoid returning `null`.
- Prefer `Stream` and `Collectors` for transformations; avoid imperative loops when functional is clearer.
- Use `record` for DTOs/immutables when applicable.
- Use `sealed` classes/interfaces and pattern matching when they help model the domain.

## Package structure (Clean Architecture)

```text
com.example.project
├── domain          # Entities, value objects, domain services, exceptions
├── application     # Use cases, ports (input/output interfaces)
├── infrastructure  # Port implementations: DB, HTTP, messaging
└── adapter         # Controllers, presenters, CLI, web
```

- Packages must not depend on external frameworks in domain/application.

## Frameworks

- **Spring Boot**: use constructor injection, avoid field `@Autowired`, prefer `@ConfigurationProperties` for config.
- **Quarkus**: prioritize constructor injection and `@ApplicationScoped`.
- **Jakarta EE / JPA**: keep persistence entities in infrastructure; domain entities are separate when needed.

## Tests

- Use JUnit 5 + AssertJ/Mockito.
- Name tests consistently: `shouldCalculateTotalWhenAddingItem`.
- Test domain units without the Spring Context. Integration tests with `@SpringBootTest` only when needed.

## Dependencies

- Do not add libraries without justification. Check existing `pom.xml` / `build.gradle`.
- Prefer libraries from the standard ecosystem (SLF4J, Jackson, etc.).
- Validate version compatibility with the project's Java.

## Logging and exceptions

- Use SLF4J. Do not log sensitive data.
- Create specific domain exceptions. Do not use generic `RuntimeException`.
- Avoid silently catching exceptions.
