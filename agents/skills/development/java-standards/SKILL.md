---
name: java-standards
version: "1.0"
description: Applies modern Java standards, Clean Code, Clean Architecture and tests. Use on `*.java` or `pom.xml`.
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

## When working with Java

1. Check the project baseline (`pom.xml`, `build.gradle`, `.java-version`).
2. Respect the existing package structure.
3. Apply Clean Code and Clean Architecture.
4. Prefer immutability, `Optional`, `Stream`, `record`.
5. Add tests with JUnit 5 + AssertJ/Mockito.
6. Do not add dependencies without checking compatibility.
7. Document public APIs with concise JavaDoc.

## Standard checks

- Names in English, per project convention.
- Do not return `null`; use `Optional` or domain exceptions.
- Separate domain entities from JPA entities when the domain is critical.
- Use constructor injection in Spring/Quarkus.
- Avoid logic in controllers; delegate to use cases/services.
