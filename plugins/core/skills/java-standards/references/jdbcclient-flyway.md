---
description: JdbcClient persistence without JPA - explicit RowMapper, named parameters, transaction boundary, receipt-based idempotency, Flyway, Testcontainers.
kind: detail
---

# Java - JdbcClient + Flyway, no JPA

## Module placement

- Repository port (interface) in `application`; the `Jdbc*Repository` in the outbound persistence adapter is package-private, `final`, and constructor-injects `JdbcClient`.

## Row mapping

- One `private static final RowMapper<T>` per row type; typed column reads, no reflection mapping. A `Timestamps`-style helper converts `Instant` to `OffsetDateTime` (UTC) on write and back on read.

```java
private static final RowMapper<Receipt> MAPPER = (rs, row) -> new Receipt(
    rs.getObject("command_id", UUID.class),
    rs.getObject("created_at", OffsetDateTime.class).toInstant());
```

## Parameters

- Prefer named parameters (`:name` in the SQL, `.param("name", value)`); positional `?` only for one-parameter statements. Never concatenate values into SQL.

## Transaction boundary

- A `TransactionRunner` port (`<T> T inTransaction(Supplier<T>)`) lives in `application`, implemented in the adapter on `TransactionTemplate`. The application service, never the repository, opens the transaction; no external I/O inside it.

## Idempotency by receipt

- Receipt table: `command_id uuid UNIQUE` (the idempotency key), `account_id`, `type`, `payload_hash bytea` with a CHECK on length (32), `result jsonb`, `created_at timestamptz`.
- The service finds the receipt first: matching `type` and `payload_hash` replays `result`, a mismatch throws; otherwise it runs the effects and inserts the receipt in the same transaction. `update() != 1` means a lost race - throw so the transaction undoes the effects, then re-read the winner's row outside.

```sql
INSERT INTO command_receipts (command_id, account_id, type, payload_hash, result, created_at)
VALUES (:commandId, :accountId, :type, :hash, :result::jsonb, :now)
ON CONFLICT ON CONSTRAINT uq_command_receipts_command_id DO NOTHING
```

- Retention: a sweep by `created_at`, never in the request path.

## Time and randomness

- `java.time.Clock` and `java.util.random.RandomGenerator` are constructor parameters of application and domain classes. Production wiring supplies `Clock.systemUTC()` and a seeded or default generator in the configuration class only; tests pass `Clock.fixed(...)` and a seeded generator.

## Flyway

- `src/main/resources/db/migration/V<n>__<slug>.sql`: forward-only, one concern per file, integrity (CHECK, UNIQUE, FK) in the migration. Never edit an applied migration (add `V<n+1>`), never `ddl-auto`, never `flyway:clean` outside a throwaway database.

## Integration test

- Testcontainers PostgreSQL; run Flyway against the container before the tests, wire with `JdbcClient.create(dataSource)`, truncate between tests; class suffix `IT`. For `@ServiceConnection` and container reuse, see the Testcontainers reference.
