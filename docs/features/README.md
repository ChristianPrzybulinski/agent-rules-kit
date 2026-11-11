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
| [`KIT-007-shell-zsh-traps.md`](KIT-007-shell-zsh-traps.md) | done | #81 | #84 |
| [`KIT-008-measure-before-parallelizing.md`](KIT-008-measure-before-parallelizing.md) | done | #82 | #87 |
| [`KIT-009-read-ahead.md`](KIT-009-read-ahead.md) | done | #83 | #86 |
| [`KIT-010-auto-compact-window.md`](KIT-010-auto-compact-window.md) | done | #88 | #89 |
| [`KIT-011-github-connectivity-before-authentication.md`](KIT-011-github-connectivity-before-authentication.md) | done | #90 | #91 |
| [`KIT-012-loop-orchestrate-lease.md`](KIT-012-loop-orchestrate-lease.md) | done | #92 | #93 |
| [`KIT-013-refresh-reinstalls-changed-claude-plugins.md`](KIT-013-refresh-reinstalls-changed-claude-plugins.md) | done | #94 | #96 |
| [`KIT-014-kit-ci-on-demand.md`](KIT-014-kit-ci-on-demand.md) | done | #97 | #99 |
| [`KIT-015-proportional-validation.md`](KIT-015-proportional-validation.md) | done | #100 | #101 |
| [`KIT-016-multi-profile-sync.md`](KIT-016-multi-profile-sync.md) | done | #102 | #103 |
| [`KIT-017-sticky-profile-list.md`](KIT-017-sticky-profile-list.md) | done | #104 | #105 |
| [`KIT-018-core-browser-preference.md`](KIT-018-core-browser-preference.md) | done | #107 | #108 |
| [`KIT-019-release-bump-command.md`](KIT-019-release-bump-command.md) | done | #110 | #112 |
| [`KIT-021-synced-folder-warning.md`](KIT-021-synced-folder-warning.md) | done | #114 | #117 |
| [`KIT-022-launchd-path-and-skips.md`](KIT-022-launchd-path-and-skips.md) | done | #115 | #118 |
| [`KIT-023-shared-codex-lookup.md`](KIT-023-shared-codex-lookup.md) | done | #116 | #119 |
| [`KIT-024-loop-tool-destination.md`](KIT-024-loop-tool-destination.md) | done | #122 | #123 |
| [`KIT-025-public-mit-license.md`](KIT-025-public-mit-license.md) | done | #124 | #125 |
| [`KIT-026-pgrep-wait-lists-matches.md`](KIT-026-pgrep-wait-lists-matches.md) | done | #126 | #127 |
| [`KIT-027-device-owner-in-handoff.md`](KIT-027-device-owner-in-handoff.md) | done | #128 | #129 |
| [`KIT-028-writer-line-in-state-file.md`](KIT-028-writer-line-in-state-file.md) | done | #130 | #138 |

[`TEMPLATE.md`](TEMPLATE.md) is the file to copy.
