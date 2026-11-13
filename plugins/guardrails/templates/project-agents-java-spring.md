# AGENTS.md — Java + Spring Boot

Replace the passages between [brackets]; a line that starts with [JdbcClient] or [JPA] is kept whole or deleted whole according to the persistence choice. The AI Kit's global rules already apply; here only what the agent cannot infer.

## Stack

- Java 25 LTS (`maven.compiler.release=25`, the kit's fixed LTS), Spring Boot [4.1.x] (never 3.5.x: out of OSS support since 2026-06-30). Build via the Maven wrapper: `./mvnw`. Never global `mvn`, never Gradle.
- Tests: JUnit 5 + AssertJ + Mockito. Integration: Testcontainers. Formatting: Spotless (source of truth — do not duplicate style here).
- Database: [PostgreSQL]; Flyway migrations in `src/main/resources/db/migration/V*.sql`.

## Choices (pick one per line, delete the other)

- Persistence, declared choice: [JdbcClient + hand-written SQL + Flyway, no JPA/Hibernate | Spring Data JPA + Flyway]. Decision record: [docs/spec/decisions/DEC-nnn-*.md | docs/adr/nnnn-*.md]. Delete the option not chosen and every line below tagged with the other option.
- Errors, declared choice: [RFC 9457 `ProblemDetail` via `@ControllerAdvice` | project error catalog `{code, message, details?}` mapped in the inbound adapter]. Delete the option not chosen.

## Structure

```text
src/main/java/[com/example/app]
├── domain/         # entities, value objects, domain exceptions; no Spring, JDBC or JPA imports
├── application/    # use cases + ports (interfaces)
├── adapter/        # in: controllers or WS handlers, DTOs, mappers | out: repositories (JdbcClient or JPA), HTTP clients
└── infrastructure/ # Spring config, beans, security
src/test/java       # mirrors main
```

## Commands

```bash
./mvnw spring-boot:run                    # run locally
./mvnw test                               # unit
./mvnw -Dtest=SomeTest test               # one test
./mvnw verify                             # unit + integration
./mvnw spotless:apply                     # format
./mvnw spotless:check verify              # gate before commit/PR
```

## Patterns (condition → action)

- Create a bean → constructor injection; `final` class with `private final` fields. Never field `@Autowired`.
- Expose an endpoint → `record` DTO in/out; a persistence entity or row mapping never leaves the adapter.
- Value may be absent → `Optional` in the return; never `null`. A parameter is never `Optional`.
- Business error → specific domain exception in `domain/`; the inbound adapter converts it to the declared error format (RFC 9457 `ProblemDetail` or the catalog `{code, message, details?}`); never a generic 500 and never a stack trace in the body.
- [JdbcClient] Query → repository port in `application/`, `JdbcClient` adapter with named parameters and an explicit `RowMapper`; never SQL built by string concatenation.
- [JPA] Filtered query → `Specification` or named query method; avoid string JPQL when a typed alternative exists.
- Config → `@ConfigurationProperties` + `record`; no scattered `@Value`.
- Log → SLF4J with placeholders; never concatenate; never log sensitive data.
- New domain test → no `@SpringBootTest`; pure JUnit. `@SpringBootTest` only for real integration.

Example — use case with a port:

```java
public final class CreateOrder {
    private final OrderRepository repo;
    public CreateOrder(OrderRepository repo) { this.repo = repo; }
    public Order execute(NewOrder cmd) {
        var order = Order.create(cmd.customerId(), cmd.items());
        return repo.save(order);
    }
}
```

## Git & PR

1. `git switch -c feat/<short-name>` from `main`.
2. Conventional Commits.
3. Before pushing: `./mvnw spotless:check verify` green.
4. `gh pr create` with: 1-line summary, what you tested, `Closes #N`.

## Boundaries

- Always: a new migration for a schema change; a test for a fixed bug; read `application.yml` before assuming config.
- Ask first: change `pom.xml`; edit an already-applied migration; change Spring auto-config; change a public API contract.
- Never: `@Disabled` to go green; `.env` or credentials in the repo; [JPA] `ddl-auto=update` outside tests; [JdbcClient] JPA annotations or `EntityManager` anywhere.

## More

- Layer boundaries: `docs/architecture.md`. Decisions: `docs/adr/`.
