# docs/features/ — confirmed kit improvements

Scope: one file per kit improvement the owner confirmed, so the reason, the evidence and the change stay with the kit.
A kit improvement is implemented by hand in a kit session. It never goes through a project's review loop: the kit is
not one of the loop's repositories, and it serves more than one project.

## Process

1. A session (a project's improvement notes, an assessment under [`../plans/`](../plans/README.md), a review) proposes a
   kit change with its evidence. Nothing is written here until the owner confirms it.
2. On confirmation: copy [`TEMPLATE.md`](TEMPLATE.md) to `KIT-NNN-<slug>.md` (next free number), and open one issue in
   this repository titled `[KIT-NNN] <title>`, label `kit-feature`, that links the file.
3. The PR that implements it closes the issue (`Closes #N`); its `CHANGELOG.md` line cites `KIT-NNN`. The file's
   `status` becomes `done`, and the file records the PR.
4. A confirmed improvement that is later dropped keeps its file with `status: dropped` and the reason.

Statuses: `confirmed` → `done` | `dropped`.

## Features

| File | Status | Issue | PR |
|---|---|---|---|
| [`KIT-001-pre-existing-needs-a-baseline.md`](KIT-001-pre-existing-needs-a-baseline.md) | done | #69 | #68 |
| [`KIT-002-no-vendored-core-skills.md`](KIT-002-no-vendored-core-skills.md) | done | #71 | #72 |
| [`KIT-003-smoke-fixture-no-auto-maintenance.md`](KIT-003-smoke-fixture-no-auto-maintenance.md) | done | #73 | #74 |
| [`KIT-004-parallel-spec-id-blocks.md`](KIT-004-parallel-spec-id-blocks.md) | confirmed | #75 | — |
| [`KIT-005-gates-need-a-full-checkout.md`](KIT-005-gates-need-a-full-checkout.md) | done | #77 | #78 |
| [`KIT-006-spec-check-rejects-conflict-markers.md`](KIT-006-spec-check-rejects-conflict-markers.md) | done | #79 | #80 |
| [`KIT-007-shell-zsh-traps.md`](KIT-007-shell-zsh-traps.md) | done | #81 | #? |

[`TEMPLATE.md`](TEMPLATE.md) is the file to copy.
