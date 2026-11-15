---
description: PostgreSQL backup and restore proof behind a release's rollback plan. Load when a release changes stored data or switches on a flag that writes it.
kind: detail
---

# Backup and restore

The data step of a release's rollback plan (`sdd-release` § 5). Migration always/never: rule `migrations.md`; schema design: skill `sdd-plan`, reference `data.md`.

- Run a daily `pg_dump -Fc`, and add WAL archiving when the recovery point objective is under 24 hours.
- Before a release that changes stored data, take a fresh dump and name it in the rollback plan.
- Prove the dump: `pg_restore` into an empty database, then run a smoke query, and paste the literal output; an untested dump is no backup.
- Keep dumps outside the repository and outside the Docker volume they protect.
- `DROP`, `TRUNCATE` and an unbounded `DELETE` stay ask-first, in a rollback too.

Done when: the rollback plan names the dump, its restore was proven with command output, and the dump lives outside the repository and the volume.
