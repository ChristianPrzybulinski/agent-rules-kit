---
description: "Testcontainers in Spring Boot and plain JUnit: @ServiceConnection beans, when static @Container is safe, local reuse, sandbox caching."
kind: fact
verified: "2026-10-06"
sources:
  - https://docs.spring.io/spring-boot/4.1/reference/testing/testcontainers.html
  - https://java.testcontainers.org/features/reuse/
---

# Testcontainers — Spring Boot and plain JUnit

## Spring context tests

A `@SpringBootTest` or slice test that needs a real service declares the container as a Spring bean in a `@TestConfiguration(proxyBeanMethods = false)` class, tagged `@ServiceConnection` (from the `spring-boot-testcontainers` module), and applies it with `@Import` on the test class:

```java
@TestConfiguration(proxyBeanMethods = false)
class TestcontainersConfig {
    @Bean
    @ServiceConnection
    PostgreSQLContainer postgres() {
        return new PostgreSQLContainer("postgres:18");
    }
}
```

Why: the JUnit extension starts and stops a `static @Container` per test class, while the TestContext Framework can cache the `ApplicationContext` beyond that point — a cached `DataSource` then points at a stopped container. Testcontainers 2.x container classes are not generic: write `PostgreSQLContainer`, never `PostgreSQLContainer<?>`. When no bean is needed, the JDBC-URL shortcut `jdbc:tc:postgresql:<ver>:///db` (driver `ContainerDatabaseDriver`, one container per URL) is the acceptable alternative.

## Plain JUnit (no Spring)

`@Testcontainers` + `static @Container` is correct: no cached context exists. Keep one container per class and truncate between tests instead of restarting it.

## Local reuse

`testcontainers.reuse.enable=true` in `~/.testcontainers.properties` plus `.withReuse(true)` on the container keeps it running between local runs. The kit's sync never writes that file — per-developer opt-in only; CI never reuses.

## Sandbox / offline runs

`-o` covers Maven artifacts, never Docker images: the image must already be in the local Docker cache (the snapshot step of `build-and-dependencies.md` pulls it). No Docker → unit scope only; say so in the PR instead of faking a green `verify`.
