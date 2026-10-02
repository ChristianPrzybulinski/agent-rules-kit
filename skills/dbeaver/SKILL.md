---
name: dbeaver
description: DBeaver GUI inspection. Use when inspecting a database, exporting test data or drawing an ER diagram. Not for schema changes (skill postgresql).
argument-hint: "[connect | export | er-diagram]"
triggers:
  - user
allowed-tools:
  - read
  - exec
---

# DBeaver

DBeaver is a human inspection tool; Flyway remains the schema source of truth.

## 1. Connect safely

Read host/port/database/user from `.env` without printing the password. Connect to local PostgreSQL on `127.0.0.1`, store credentials in the OS keychain and never commit DBeaver workspace/connection files.

## 2. Inspect or export data

Use read-only queries by default. For reusable test data, prefer a versioned `pg_dump --data-only --table=<table>` fixture over a GUI export. Never copy real personal data; anonymize before export.

Ask before any destructive statement or `UPDATE`/`DELETE` without `WHERE`, even when the GUI offers confirmation.

## 3. Produce an ER diagram

Export schema ER output as `docs/architecture/er-<date>.svg`; mark it derived and include the current Flyway migration version so staleness is visible.

## 4. Route schema changes

A GUI schema edit in a disposable database is exploratory only. Recreate every accepted change as the next `V<n>__slug.sql` and verify through the PostgreSQL migration workflow.

Done when: connection secrets remain outside the repository, exports contain no personal data, diagrams name their migration and schema changes exist as Flyway files.
