# docs/features/ — confirmed kit improvements

Scope: one file per kit improvement the owner confirmed, so the reason, the evidence and the change stay with the kit.
A kit improvement is implemented by hand in a kit session. It never goes through a project's review loop: the kit is
not one of the loop's repositories, and it serves more than one project.

## Process

A record is for a big change only: a hook, `plugins/core/AGENTS.md`, plugin structure or manifests, a check, gate or
script behavior change, or a new or removed skill. Any other change (a skill, rule, reference, template or doc text
edit) needs only its `CHANGELOG.md` line, and the PR body carries the why (KIT-040). Records written before KIT-040 stay
as they are.

1. A session (a project's improvement notes, an assessment, a review) proposes a kit change with its evidence. Nothing
   is written here until the owner confirms it.
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
| [`KIT-020-guard-merged-branch-delete.md`](KIT-020-guard-merged-branch-delete.md) | done | #113 | #185 |
| [`KIT-021-synced-folder-warning.md`](KIT-021-synced-folder-warning.md) | done | #114 | #117 |
| [`KIT-022-launchd-path-and-skips.md`](KIT-022-launchd-path-and-skips.md) | done | #115 | #118 |
| [`KIT-023-shared-codex-lookup.md`](KIT-023-shared-codex-lookup.md) | done | #116 | #119 |
| [`KIT-024-loop-tool-destination.md`](KIT-024-loop-tool-destination.md) | done | #122 | #123 |
| [`KIT-025-public-mit-license.md`](KIT-025-public-mit-license.md) | done | #124 | #125 |
| [`KIT-026-pgrep-wait-lists-matches.md`](KIT-026-pgrep-wait-lists-matches.md) | done | #126 | #127 |
| [`KIT-027-device-owner-in-handoff.md`](KIT-027-device-owner-in-handoff.md) | done | #128 | #129 |
| [`KIT-028-writer-line-in-state-file.md`](KIT-028-writer-line-in-state-file.md) | done | #130 | #138 |
| [`KIT-029-design-and-type-principles.md`](KIT-029-design-and-type-principles.md) | done | #131 | #139 |
| [`KIT-030-test-honesty-and-parity.md`](KIT-030-test-honesty-and-parity.md) | done | #132 | #140 |
| [`KIT-031-complexity-signal.md`](KIT-031-complexity-signal.md) | done | #133 | #141 |
| [`KIT-032-process-sharpenings-and-decisions.md`](KIT-032-process-sharpenings-and-decisions.md) | done | #134 | #142 |
| [`KIT-033-gdscript-duplicate-finder.md`](KIT-033-gdscript-duplicate-finder.md) | done | #135 | #143 |
| [`KIT-034-gdscript-coverage.md`](KIT-034-gdscript-coverage.md) | confirmed | #136 | — |
| [`KIT-035-gdscript-mutation.md`](KIT-035-gdscript-mutation.md) | confirmed | #137 | — |
| [`KIT-036-eval-login-check.md`](KIT-036-eval-login-check.md) | done | #146 | #147 |
| [`KIT-037-evals-templates-trim.md`](KIT-037-evals-templates-trim.md) | done | #148 | #149 |
| [`KIT-038-three-plugins.md`](KIT-038-three-plugins.md) | done | #151 | #153 |
| [`KIT-039-skill-merges.md`](KIT-039-skill-merges.md) | done | #154 | #155 |
| [`KIT-040-ceremony-cut.md`](KIT-040-ceremony-cut.md) | done | #150 | #152 |
| [`KIT-041-eval-plugin-deps.md`](KIT-041-eval-plugin-deps.md) | done | #156 | #158 |
| [`KIT-042-root-docs-and-readmes.md`](KIT-042-root-docs-and-readmes.md) | done | #160 | #161 |
| [`KIT-043-tool-text-is-evidence.md`](KIT-043-tool-text-is-evidence.md) | done | #162 | #163 |
| [`KIT-044-positive-phrasing.md`](KIT-044-positive-phrasing.md) | done | #165 | #166 |
| [`KIT-045-python-rule.md`](KIT-045-python-rule.md) | done | #167 | #168 |
| [`KIT-046-refresh-reexec.md`](KIT-046-refresh-reexec.md) | done | #173 | #175 |
| [`KIT-047-one-plugin.md`](KIT-047-one-plugin.md) | done | #176 | #177 |
| [`KIT-050-hooks-no-verify-compact.md`](KIT-050-hooks-no-verify-compact.md) | done | #180 | #182 |
| [`KIT-052-plugin-links-and-not-for.md`](KIT-052-plugin-links-and-not-for.md) | done | #184 | #183 |
| [`KIT-053-guard-git-global-options.md`](KIT-053-guard-git-global-options.md) | done | #186 | #187 |
| [`KIT-054-guard-command-prefixes.md`](KIT-054-guard-command-prefixes.md) | done | #189 | #190 |

[`TEMPLATE.md`](TEMPLATE.md) is the file to copy.
