# docs/features/ — confirmed kit improvements

Scope: one file per kit improvement the owner confirmed, so the reason, the evidence and the change stay with the kit.
A kit improvement is implemented by hand in a kit session. It never goes through a project's review loop: the kit is
not one of the loop's repositories, and it serves more than one project.

## Process

A record is for a big change only: a hook, `plugins/guardrails/AGENTS.md`, plugin structure or manifests, a check, gate or
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

| File | Changed | Status | Issue | PR |
|---|---|---|---|---|
| [`KIT-001-pre-existing-needs-a-baseline.md`](KIT-001-pre-existing-needs-a-baseline.md) | pre-existing failure needs a baseline | done | #69 | #68 |
| [`KIT-002-no-vendored-core-skills.md`](KIT-002-no-vendored-core-skills.md) | vendored projects skip core skills | done | #71 | #72 |
| [`KIT-003-smoke-fixture-no-auto-maintenance.md`](KIT-003-smoke-fixture-no-auto-maintenance.md) | smoke fixture starts no maintenance | done | #73 | #74 |
| [`KIT-004-parallel-spec-id-blocks.md`](KIT-004-parallel-spec-id-blocks.md) | parallel spec id blocks, REQ included | done | #75 | #214 |
| [`KIT-005-gates-need-a-full-checkout.md`](KIT-005-gates-need-a-full-checkout.md) | gates need a full checkout | done | #77 | #78 |
| [`KIT-006-spec-check-rejects-conflict-markers.md`](KIT-006-spec-check-rejects-conflict-markers.md) | check_spec rejects conflict markers | done | #79 | #80 |
| [`KIT-007-shell-zsh-traps.md`](KIT-007-shell-zsh-traps.md) | three zsh traps; loops and JSON in Python | done | #81 | #84 |
| [`KIT-008-measure-before-parallelizing.md`](KIT-008-measure-before-parallelizing.md) | measure conflicts before parallel work | done | #82 | #87 |
| [`KIT-009-read-ahead.md`](KIT-009-read-ahead.md) | read-ahead prepare agents | done | #83 | #86 |
| [`KIT-010-auto-compact-window.md`](KIT-010-auto-compact-window.md) | doctor caps the auto-compact window | done | #88 | #89 |
| [`KIT-011-github-connectivity-before-authentication.md`](KIT-011-github-connectivity-before-authentication.md) | GitHub connectivity vs authentication | done | #90 | #91 |
| [`KIT-012-loop-orchestrate-lease.md`](KIT-012-loop-orchestrate-lease.md) | loop-orchestrate takes the lease first | done | #92 | #93 |
| [`KIT-013-refresh-reinstalls-changed-claude-plugins.md`](KIT-013-refresh-reinstalls-changed-claude-plugins.md) | refresh.sh reinstalls changed plugins | done | #94 | #96 |
| [`KIT-014-kit-ci-on-demand.md`](KIT-014-kit-ci-on-demand.md) | kit CI on demand only | done | #97 | #99 |
| [`KIT-015-proportional-validation.md`](KIT-015-proportional-validation.md) | validation and review sized by impact | done | #100 | #101 |
| [`KIT-016-multi-profile-sync.md`](KIT-016-multi-profile-sync.md) | multi-profile project sync | done | #102 | #103 |
| [`KIT-017-sticky-profile-list.md`](KIT-017-sticky-profile-list.md) | sync keeps the profile list | done | #104 | #105 |
| [`KIT-018-core-browser-preference.md`](KIT-018-core-browser-preference.md) | browser preference in core rules | done | #107 | #108 |
| [`KIT-019-release-bump-command.md`](KIT-019-release-bump-command.md) | one release bump command | done | #110 | #112 |
| [`KIT-020-guard-merged-branch-delete.md`](KIT-020-guard-merged-branch-delete.md) | guard allows deleting a merged PR branch | done | #113 | #185 |
| [`KIT-021-synced-folder-warning.md`](KIT-021-synced-folder-warning.md) | cloud-synced folder warning | done | #114 | #117 |
| [`KIT-022-launchd-path-and-skips.md`](KIT-022-launchd-path-and-skips.md) | launchd refresh PATH and skips | done | #115 | #118 |
| [`KIT-023-shared-codex-lookup.md`](KIT-023-shared-codex-lookup.md) | one Codex CLI lookup | done | #116 | #119 |
| [`KIT-024-loop-tool-destination.md`](KIT-024-loop-tool-destination.md) | review-loop tool's home | done | #122 | #123 |
| [`KIT-025-public-mit-license.md`](KIT-025-public-mit-license.md) | public MIT license | done | #124 | #125 |
| [`KIT-026-pgrep-wait-lists-matches.md`](KIT-026-pgrep-wait-lists-matches.md) | pgrep wait lists its matches | done | #126 | #127 |
| [`KIT-027-device-owner-in-handoff.md`](KIT-027-device-owner-in-handoff.md) | handoff names a shared device's owner | done | #128 | #129 |
| [`KIT-028-writer-line-in-state-file.md`](KIT-028-writer-line-in-state-file.md) | state file names its writer | done | #130 | #138 |
| [`KIT-029-design-and-type-principles.md`](KIT-029-design-and-type-principles.md) | design and type principles | done | #131 | #139 |
| [`KIT-030-test-honesty-and-parity.md`](KIT-030-test-honesty-and-parity.md) | test honesty and language parity | done | #132 | #140 |
| [`KIT-031-complexity-signal.md`](KIT-031-complexity-signal.md) | advisory complexity script | done | #133 | #141 |
| [`KIT-032-process-sharpenings-and-decisions.md`](KIT-032-process-sharpenings-and-decisions.md) | process sharpenings, FEAT Decisions log | done | #134 | #142 |
| [`KIT-033-gdscript-duplicate-finder.md`](KIT-033-gdscript-duplicate-finder.md) | GDScript duplicate finder | done | #135 | #143 |
| [`KIT-034-gdscript-coverage.md`](KIT-034-gdscript-coverage.md) | advisory GDScript coverage tool | done | #136 | #191, #193, #194, #196, #218 |
| [`KIT-035-gdscript-mutation.md`](KIT-035-gdscript-mutation.md) | advisory GDScript mutation tool | done | #137 | #192, #195, #196, #200, #218 |
| [`KIT-036-eval-login-check.md`](KIT-036-eval-login-check.md) | eval run checks the CLI login | done | #146 | #147 |
| [`KIT-037-evals-templates-trim.md`](KIT-037-evals-templates-trim.md) | trigger evals; no doc-* templates in plugins | done | #148 | #149 |
| [`KIT-038-three-plugins.md`](KIT-038-three-plugins.md) | three plugins by audience | done | #151 | #153 |
| [`KIT-039-skill-merges.md`](KIT-039-skill-merges.md) | skill merges, 38 to 27 | done | #154 | #155 |
| [`KIT-040-ceremony-cut.md`](KIT-040-ceremony-cut.md) | records for big changes, generated indexes | done | #150 | #152 |
| [`KIT-041-eval-plugin-deps.md`](KIT-041-eval-plugin-deps.md) | eval cases load core | done | #156 | #158 |
| [`KIT-042-root-docs-and-readmes.md`](KIT-042-root-docs-and-readmes.md) | root docs into README and CONTRIBUTING | done | #160 | #161 |
| [`KIT-043-tool-text-is-evidence.md`](KIT-043-tool-text-is-evidence.md) | tool text is evidence | done | #162 | #163 |
| [`KIT-044-positive-phrasing.md`](KIT-044-positive-phrasing.md) | positive phrasing of soft rules | done | #165 | #166 |
| [`KIT-045-python-rule.md`](KIT-045-python-rule.md) | Python path rule and profile | done | #167 | #168 |
| [`KIT-046-refresh-reexec.md`](KIT-046-refresh-reexec.md) | refresh.sh reruns its pulled version | done | #173 | #175 |
| [`KIT-047-one-plugin.md`](KIT-047-one-plugin.md) | one plugin: dev and sdd into core | done | #176 | #177 |
| [`KIT-050-hooks-no-verify-compact.md`](KIT-050-hooks-no-verify-compact.md) | guard blocks --no-verify; git state after compaction | done | #180 | #182 |
| [`KIT-052-plugin-links-and-not-for.md`](KIT-052-plugin-links-and-not-for.md) | check_kit: plugin links and 'Not for' | done | #184 | #183 |
| [`KIT-053-guard-git-global-options.md`](KIT-053-guard-git-global-options.md) | guard: git global options | done | #186 | #187 |
| [`KIT-054-guard-command-prefixes.md`](KIT-054-guard-command-prefixes.md) | guard: command prefixes | done | #189 | #190 |
| [`KIT-055-plugin-renamed-guardrails.md`](KIT-055-plugin-renamed-guardrails.md) | plugin renamed to guardrails | done | #188 | #197 |
| [`KIT-056-cross-session-audit.md`](KIT-056-cross-session-audit.md) | weekly cross-session audit | done | #204 | #205 |
| [`KIT-057-always-on-rules-review.md`](KIT-057-always-on-rules-review.md) | always-on rules review | done | #202 | #203 |
| [`KIT-058-hooks-review.md`](KIT-058-hooks-review.md) | hooks review | done | #206 | #208 |
| [`KIT-059-path-rules-review.md`](KIT-059-path-rules-review.md) | path rules review | done | #209 | #210 |
| [`KIT-060-shell-syntax-check.md`](KIT-060-shell-syntax-check.md) | shell syntax check | done | #211 | #212 |
| [`KIT-061-skills-review.md`](KIT-061-skills-review.md) | skills review | done | #213 | #214 |
| [`KIT-062-stale-plugin-folders.md`](KIT-062-stale-plugin-folders.md) | stale plugin folder scan | done | #215 | #216 |
| [`KIT-063-codeql-secret-scanning.md`](KIT-063-codeql-secret-scanning.md) | CodeQL and secret scanning | done | #221 | #222 |
| [`KIT-064-project-decision-kinds.md`](KIT-064-project-decision-kinds.md) | project decision kinds | done | #225 | #226 |
| [`KIT-065-owner-review-autonomy.md`](KIT-065-owner-review-autonomy.md) | owner-review autonomy | done | #229 | #230 |
| [`KIT-066-need-intake.md`](KIT-066-need-intake.md) | NEED intake and front chain | done | #231 | #232 |
| [`KIT-067-sdd-parameters.md`](KIT-067-sdd-parameters.md) | sdd: block parameters | done | #234 | #236 |
| [`KIT-068-plan-and-tasks-cut.md`](KIT-068-plan-and-tasks-cut.md) | one FEAT per delivery, task cut | done | #243 | #244 |
| [`KIT-069-delivery-side.md`](KIT-069-delivery-side.md) | SDD delivery side and review scripts | done | #242 | #246 |
| [`KIT-070-standards-into-rules.md`](KIT-070-standards-into-rules.md) | coding standards into path rules | done | #256 | #261 |
| [`KIT-071-guaranteed-skill-use.md`](KIT-071-guaranteed-skill-use.md) | guaranteed skill use | done | #233 | #235 |
| [`KIT-072-kit-version-pin.md`](KIT-072-kit-version-pin.md) | consumer kit version pin | done | #257 | #260 |
| [`KIT-073-spec-tools.md`](KIT-073-spec-tools.md) | spec tools: spec_trace, row_checks | done | #259 | #262 |
| [`KIT-074-dev-standards.md`](KIT-074-dev-standards.md) | generic dev standards | done | #258 | #263 |
| [`KIT-075-followups.md`](KIT-075-followups.md) | KIT-069 follow-ups | done | #284 | #285 |
| [`KIT-076-ci-on-pull-requests.md`](KIT-076-ci-on-pull-requests.md) | CI on pull requests | done | #264 | #272 |
| [`KIT-077-layered-gate-review-bar.md`](KIT-077-layered-gate-review-bar.md) | layered gate, review bar by risk | confirmed | #281 | #286, #293 |
| [`KIT-078-docs-consistency.md`](KIT-078-docs-consistency.md) | 13.0.0 docs consistency | done | #290 | #292 |
| [`KIT-079-correctness-fixes.md`](KIT-079-correctness-fixes.md) | 13.0.x correctness fixes | done | #295 | #296 |
| [`KIT-080-issue-bundle-13-1.md`](KIT-080-issue-bundle-13-1.md) | 13.1.0 issue bundle | done | #300 | #301 |
| [`KIT-081-no-copies-in-projects.md`](KIT-081-no-copies-in-projects.md) | the kit copies nothing into a project | confirmed | #308 | |
| [`KIT-082-fewer-check-kit-runs.md`](KIT-082-fewer-check-kit-runs.md) | fewer check_kit runs, gdtoolkit in CI | done | #311 | #312 |
| [`KIT-083-kit-081-review-follow-ups.md`](KIT-083-kit-081-review-follow-ups.md) | the small findings of the KIT-081 reviews | done | #317 | #318 |
| [`KIT-084-changelog-fragments-and-status-sync.md`](KIT-084-changelog-fragments-and-status-sync.md) | changelog fragments, status-sync PR and gitleaks action from the kit | in-progress | #319 | |
| [`KIT-085-no-project-justfile.md`](KIT-085-no-project-justfile.md) | no project justfile: skill sdd-implement runs the kit's just modules | in-progress | #320 | |
| [`KIT-086-journeys-folding-cut.md`](KIT-086-journeys-folding-cut.md) | journeys and processes, decision folding, task cut checklist | in-progress | #321 | |
| [`KIT-087-project-profile.md`](KIT-087-project-profile.md) | one project profile read only by the kit | in-progress | #322 | |
| [`KIT-088-profile-kinds.md`](KIT-088-profile-kinds.md) | profile kind presets and game and FEAT-only keys | in-progress | #329 | |
| [`KIT-089-vision-pillars.md`](KIT-089-vision-pillars.md) | spec.md templates per kind, pillars and out-of-scope triage | in-progress | #330 | |
| [`KIT-090-process-artifact.md`](KIT-090-process-artifact.md) | process artifact PROC-nnn and its trace tools | in-progress | #331 | |
| [`KIT-092-process-verify-skills.md`](KIT-092-process-verify-skills.md) | skills that use and verify processes | in-progress | #333 | |
| [`KIT-093-plan-assets.md`](KIT-093-plan-assets.md) | Assets Plan section and sdd-check C15 | in-progress | #334 | |

[`TEMPLATE.md`](TEMPLATE.md) is the file to copy.
