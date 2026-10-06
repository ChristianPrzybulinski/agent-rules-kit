# AGENTS.md — Java + Spring Boot

Replace the passages between [brackets]. The AI Kit's global rules already apply; here only what the agent cannot infer.

## Stack

- Java [25] LTS, Spring Boot [4.x]. Build via wrapper: `./mvnw` (or `./gradlew`). Never global `mvn`.
- Tests: JUnit 5 + AssertJ + Mockito. Integration: Testcontainers. Formatting: Spotless (source of truth — do not duplicate style here).
- Database: [PostgreSQL]; Flyway migrations in `src/main/resources/db/migration/V*.sql`.

## Choices (pick one per line, delete the other)

- Persistence: `JdbcClient + Flyway` (default) | `JPA`
- Errors: `project protocol catalog` | `RFC 7807`

## Structure

```text
src/main/java/[com/example/app]
├── domain/         # entities, value objects, domain exceptions — no Spring/persistence
├── application/    # use cases + ports (interfaces)
├── adapter/        # in: controllers, DTOs, mappers | out: persistence adapters, HTTP clients
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
- Expose an endpoint → `record` DTO in/out; a persistence entity never leaves the adapter.
- Value may be absent → `Optional` in the return; never `null`. A parameter is never `Optional`.
- Business error → specific domain exception in `domain/`; `@ControllerAdvice` converts to the chosen error format (protocol catalog entry or RFC 7807 `ProblemDetail`).
- Filtered query → `JdbcClient` SQL (default) or `Specification`/named query method (JPA option); avoid string JPQL when a typed alternative exists.
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
- Ask first: change `pom.xml`/`build.gradle`; edit an already-applied migration; change Spring auto-config; change a public API contract.
- Never: `@Disabled` to go green; `.env` or credentials in the repo; `ddl-auto=update` in production.

## More

- Layer boundaries: `docs/architecture.md`. Decisions: `docs/adr/`.
