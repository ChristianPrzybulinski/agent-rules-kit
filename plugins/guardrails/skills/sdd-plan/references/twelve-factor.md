---
description: Twelve-Factor configuration, backing services, build/release/run, disposable processes and parity for a service a FEAT adds or changes. Load when planning one.
kind: detail
---

# Twelve-Factor service design

Plan § Design and § Dependencies hold these choices for a service the delivery adds or changes. Compose files, Dockerfiles and `.env.example`: rule `docker.md`; starting, inspecting and fixing containers on a running or remote host: skill `docker`.

## 1. Externalize configuration

- Every value that varies by environment is an environment variable; `application.yml` holds only safe defaults and `${VAR}` references.
- Typed configuration (Spring `@ConfigurationProperties`); no environment lookups scattered through domain code.

## 2. Declare dependencies and backing services

- Fixed dependencies are declared in `pom.xml` or `project.godot`; nothing relies on a machine-installed library.
- PostgreSQL, Redis, queues and APIs are attached by URL and credentials from configuration.
- PostgreSQL stays the source of truth; Redis is cache or ephemeral and the app degrades when it is unavailable (`data.md`).

## 3. Separate build, release and run

Build one immutable jar or export, inject configuration at run time and never edit a production artifact; the same artifact moves between environments.

## 4. Keep processes disposable

- Process memory is stateless; durable state lives outside.
- The app binds its own port, streams structured logs to stdout with a `correlation_id` and manages no log file.
- `SIGTERM` closes connections gracefully and completes the transaction in flight.

## 5. Preserve parity and admin discipline

- The same PostgreSQL and Redis major versions locally and in production; never H2 for persistence integration tests.
- Flyway migrations and admin tasks run as versioned commands with the app's configuration.
- Scale I/O with processes or virtual threads and CPU work with bounded pools, only after a measurement.

Done when: environment differences are configuration only, the artifact is immutable, processes are stateless and disposable, logs stream to stdout, and local service majors match production.
