---
name: twelve-factor
description: Twelve-Factor application configuration. Use when changing config, env vars, deploy behavior or Docker app config. Not for container mechanics (skill docker).
triggers:
  - user
  - model
allowed-tools:
  - read
  - grep
  - glob
  - edit
---

# Twelve-Factor Application

## 1. Externalize configuration

- Put every environment-varying value in an environment variable; `application.yml` contains only safe defaults and `${VAR}` references.
- Version `.env.example` with placeholders/comments and never version `.env`.
- Use typed configuration such as Spring `@ConfigurationProperties`; do not scatter environment lookups through domain code.

## 2. Declare dependencies and backing services

- Declare fixed dependencies in `pom.xml` or `project.godot`; do not rely on machine-installed libraries.
- Attach Postgres, Redis, queues and APIs by URL/credentials from config.
- PostgreSQL remains the source of truth; Redis is cache/ephemeral and the app degrades when it is unavailable.

## 3. Separate build, release and run

Build one immutable jar/export, inject configuration at run time and never edit a production artifact. The same artifact moves between environments.

## 4. Keep processes disposable

- Keep process memory stateless; persist durable state externally.
- Bind the app's own port, stream structured logs to stdout with `correlation_id`, and create no app-managed log file.
- Handle `SIGTERM` with graceful connection closure and transaction completion.

## 5. Preserve parity and admin discipline

- Use the same Postgres/Redis major versions locally and in production; do not substitute H2 for persistence integration tests.
- Run Flyway migrations and admin tasks as versioned commands with the same configuration as the app.
- Scale I/O with processes/virtual threads and CPU work with bounded pools only after measurement.

Done when: environment differences are config-only, artifacts are immutable, processes are stateless/disposable, logs stream to stdout, and local service majors match production.
