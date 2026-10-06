# prompts/ — one self-contained prompt per plan item

Each file is the first message of a fresh session (Claude Code or Devin) opened in the target repository. Paste it whole. Every prompt carries its own evidence, the exact current lines it changes, numbered steps, acceptance criteria as commands, the conventions the kit validator enforces, and the report format. Nothing else from the assessment is required; `../assessment.md` is background only.

## Order and dependencies

Run phase 1 first, then phase 2, then phase 3: a phase starts only after the previous one is merged, so a dependency on an earlier phase is already met. Inside a phase use the order below; it is derived from the Depends on column and from the files two prompts both edit (shared files: `plugins/core/AGENTS.md`, `ci-godot.yml`, `sync-project.sh`, `hooks.json`, `check_kit.py`, the `architect-sdd` skills and `sdd-process.md`, `docs/design.md`). A prompt whose dependency is not merged yet waits. Two prompts that touch the same file (see the files column) are run one after the other, never in parallel. Line numbers quoted in a prompt are those of the tree before the earlier prompts of the list; when they drift, every prompt says to match the quoted text.

### Run order inside each phase

Phase 1:

1. `P1-01` (first on `docs/design.md`, `sync-project.sh`, `docs/maintenance.md`)
2. `P1-02` (stratics-docs only; independent, its stale-path hits are what the P1-01 gate reports)
3. `P1-03` (first on `plugins/core/AGENTS.md`; next on it: P2-03, then P2-09)
4. `P1-04` (Godot skill and template movement text)
5. `P1-06` (before P1-05: both edit `ci-godot.yml`; chain continues with P1-05, then P3-02)
6. `P1-05` (after P1-06)
7. `P1-07` (first on `hooks.json` and `check_kit.py`; after P1-01 because both edit `docs/design.md`)
8. `P1-08` (first on the `architect-sdd` skills; after P1-05 and P1-06 on `platforms/kits/github/README.md`)

Phase 2:

1. `P2-01` (after P1-01 on `docs/projects.md`)
2. `P2-02` (after P1-04 to P1-07; first on the rule files)
3. `P2-03` (after P1-03 on `AGENTS.md`)
4. `P2-04` (after P1-01 on `sync-project.sh`)
5. `P2-05` (after P2-04)
6. `P2-06` (after P2-04 and P2-05; last phase 2 edit of `sync-project.sh` before P2-15)
7. `P2-07` (after P1-07 and P2-02 on `hooks.json` and `check_kit.py`)
8. `P2-08` (stratics repos; after P1-08)
9. `P2-09` (after P2-03 on `AGENTS.md` and P2-02 on the rules)
10. `P2-10` (after P2-09 and P2-07; edits `check_kit.py`, `smoke.sh`, `README.md`, `INDEX.md` on top of P2-05 to P2-07)
11. `P2-11` (independent, runs after P2-10 only to keep one kit index state)
12. `P2-12` (after P2-01)
13. `P2-13` (after P2-12)
14. `P2-14` (after P2-12 and P2-13; also edits stratics-server)
15. `P2-15` (last: after P2-04 to P2-06 and P2-08; runs after P2-09 to P2-11 so the vendored skills are the final ones)

Phase 3:

1. `P3-01` (Godot references; after P1-04 to P1-06)
2. `P3-02` (after P1-05 on `ci-godot.yml` and after P3-01 on `godot-standards`)
3. `P3-03` (after P2-02, P2-03, P2-14 and P3-02)
4. `P3-06` (first phase 3 edit of the `architect-sdd` skills and the `sdd-process.md` step table; after P1-08)
5. `P3-04` (after P3-06 on `sdd-process.md`; the stratics-docs half also needs P2-08)
6. `P3-05` (after P3-06 and P3-04 on `sdd-process.md` and the plugin index)
7. `P3-07` (after P3-06 and P1-08 on `sdd-implement`)
8. `P3-10` (after P2-15 on `sync-project.sh` and after P3-04, P3-06, P3-07 on the SDD files)
9. `P3-08` (after P1-08, P2-09, P2-10 and P3-03 on `platforms/kits/INDEX.md`)
10. `P3-11` (after P3-07 on `validate-implementation`; after P3-03 and P3-08 on `platforms/kits/INDEX.md`)
11. `P3-09` (last: after P2-07, P2-09, P2-10, P3-05, P3-06 on `check_kit.py` and the plugin indexes)

### Phase 1

| Prompt | Title | Repos | Depends on | Effort | Files touched |
|---|---|---|---|---|---|
| [`P1-01`](p1-01-freeze-layout-and-path-gate.md) | Freeze the 10.x layout and add a stale-path gate | kit | none | ~4 h | `kit: docs/design.md`, `kit: docs/maintenance.md`, `kit: docs/projects.md`, `kit: .github/PULL_REQUEST_TEMPLATE.md`, `kit: platforms/tools/sync-project.sh`, `kit: platforms/tools/INDEX.md`, `kit: platforms/ci/validations/test_sync_project.py`, `kit: platforms/ci/validations/INDEX.md` … |
| [`P1-02`](p1-02-fix-stale-kit-paths-in-stratics-docs.md) | Fix stale kit paths cited in stratics-docs | stratics-docs | none (P1-01 adds the kit-side gate; this prompt fixes every citation it will catch) | ~1.5 h | `docs: AGENTS.md`, `docs: docs/spec/decisions/DTEC-001-java-25-lts.md`, `docs: docs/spec/decisions/DTEC-002-stack-cliente-servidor-banco.md`, `docs: changelog.d/p1-02-stale-kit-paths.fixed.md` |
| [`P1-03`](p1-03-resolve-confidence-rule.md) | Resolve the 98% confidence rule in the global AGENTS.md | kit | none | ~1.5 h | `kit: plugins/core/AGENTS.md`, `kit: plugins/quality-core/skills/skeptic/SKILL.md`, `kit: plugins/quality-core/INDEX.md`, `kit: CHANGELOG.md` |
| [`P1-04`](p1-04-godot-movement-model-not-default.md) | Make the Godot movement model a project decision, not a kit default | kit | none | ~2 h | `kit: plugins/dev-godot/skills/godot-standards/SKILL.md`, `kit: plugins/dev-godot/templates/project-agents-godot-2d.md`, `kit: platforms/kits/godot/editor_settings_hints.md`, `kit: CHANGELOG.md` |
| [`P1-05`](p1-05-godot-tests-gdunit4-never-skip.md) | Godot tests: gdUnit4 by default, CI never skips silently, GDScript test policy | kit | P1-06 (both edit `ci-godot.yml`, `godot-standards/SKILL.md`, the Godot template and two READMEs; P1-06 merges first, and every anchor in Change step 1 still works if the order is reversed) | ~3 h | `kit: platforms/kits/github/workflows/ci-godot.yml`, `kit: platforms/kits/godot/.gitignore`, `kit: plugins/dev-godot/templates/project-agents-godot-2d.md`, `kit: plugins/dev-godot/skills/godot-standards/SKILL.md`, `kit: plugins/dev-core/skills/testing/SKILL.md`, `kit: platforms/kits/godot/README.md`, `kit: platforms/kits/github/README.md`, `kit: CHANGELOG.md` |
| [`P1-06`](p1-06-godot-boot-proof.md) | Correct the Godot boot proof (--import plus SCRIPT ERROR grep) | kit | the assessment branch merged to main (so `docs/plans/2026-10-kit-assessment/` exists); otherwise keep the Refs path as given, it resolves after that merge. No code dependency (merge before P1-05 or rebase; both touch `ci-godot.yml`) | ~2 h | `kit: platforms/kits/github/workflows/ci-godot.yml`, `kit: plugins/dev-godot/skills/godot-standards/SKILL.md`, `kit: plugins/quality-core/agents/reviewer.md`, `kit: plugins/quality-core/skills/validate-implementation/SKILL.md`, `kit: plugins/dev-godot/templates/project-agents-godot-2d.md`, `kit: platforms/kits/godot/README.md`, `kit: platforms/kits/github/README.md`, `kit: CHANGELOG.md` |
| [`P1-07`](p1-07-hook-guard-coverage.md) | Hook guard: cover what the skills promise, current JSON contract, CI cases | kit | none | ~4 h | `kit: plugins/core/hooks/hooks.json`, `kit: platforms/ci/validations/hook_guard_cases.json`, `kit: platforms/ci/validations/check_kit.py`, `kit: platforms/tools/smoke.sh`, `kit: docs/design.md`, `kit: CHANGELOG.md` |
| [`P1-08`](p1-08-sdd-absorb-architect-deltas.md) | SDD absorbs the ARCHITECT.md deltas (issue per task, waves, model directive, task template) | kit | none | ~6 h | `kit: plugins/architect-sdd/skills/sdd-tasks/SKILL.md`, `kit: plugins/architect-sdd/skills/sdd-tasks/references/waves-and-models.md`, `kit: plugins/architect-sdd/templates/spec-feature.md`, `kit: plugins/architect-sdd/skills/sdd-to-card/SKILL.md`, `kit: plugins/architect-sdd/skills/sdd-to-card/references/task-issue.md`, `kit: plugins/architect-sdd/skills/sdd-implement/SKILL.md`, `kit: plugins/architect-sdd/skills/sdd-implement/references/task-pr.md`, `kit: plugins/architect-sdd/skills/sdd-constitution/references/sdd-process.md` … |

### Phase 2

| Prompt | Title | Repos | Depends on | Effort | Files touched |
|---|---|---|---|---|---|
| [`P2-01`](p2-01-remove-machine-facts.md) | Remove machine-specific facts from kit references and docs | kit | P1-01 (its step 3 rewrites `docs/projects.md:3` and `:23`, the other two `installed on` hits) | ~1.5 h | `kit:plugins/dev-godot/skills/godot-standards/references/godot-4-versions.md`, `kit:plugins/dev-java/skills/java-standards/references/java-25-lts.md`, `kit:plugins/infra-core/skills/docker/references/compose-v2-vs-v5.md`, `kit:plugins/infra-core/skills/docker/SKILL.md`, `kit:docs/maintenance.md`, `kit:platforms/kits/java-maven/toolchains.xml.example`, `kit:CHANGELOG.md` |
| [`P2-02`](p2-02-path-rules-with-content.md) | Path-scoped rules carry real constraints, not pointers | kit (agent-rules-kit) | P1-04, P1-05, P1-06, P1-07 (same `check_kit.py`; P1-07 keeps its line count, so line 28 below holds) | ~3 h | `kit:plugins/dev-godot/rules/godot.md`, `kit:plugins/dev-java/rules/java.md`, `kit:plugins/architect-sdd/rules/spec.md`, `kit:platforms/ci/validations/check_kit.py`, `kit:INDEX.md`, `kit:docs/maintenance.md`, `kit:CHANGELOG.md` |
| [`P2-03`](p2-03-agents-md-order-and-lines.md) | Reorder the global AGENTS.md and add two lines | kit (agent-rules-kit) | P1-03 | ~1 h | `kit:plugins/core/AGENTS.md`, `kit:CHANGELOG.md` |
| [`P2-04`](p2-04-sync-project-claude-md-and-settings.md) | sync-project.sh generates CLAUDE.md and .claude/settings.json per repo profile | kit | P1-01 | ~5 h | `kit: platforms/tools/sync-project.sh`, `kit: platforms/tools/INDEX.md`, `kit: platforms/tools/smoke.sh`, `kit: platforms/ci/validations/test_sync_project.py`, `kit: docs/projects.md`, `kit: CHANGELOG.md` |
| [`P2-05`](p2-05-sync-project-rules.md) | sync-project.sh generates .claude/rules from kit rules | kit (agent-rules-kit) | P2-04 (P2-02 may land before or after) | ~4 h | `kit:platforms/tools/sync-project.sh`, `kit:platforms/tools/doctor.sh`, `kit:platforms/tools/smoke.sh`, `kit:platforms/tools/INDEX.md`, `kit:README.md`, `kit:docs/design.md`, `kit:docs/projects.md`, `kit:CHANGELOG.md` |
| [`P2-06`](p2-06-sync-project-vendored-skills.md) | sync-project.sh vendors skills into .claude/skills with a manifest | kit (agent-rules-kit) | P2-04, P2-05 (both merged to main; P1-01 arrives through P2-04). Independent of P2-09/P2-10: the generator reads the plugin list, never skill names; the literal counts below hold for the v10.1.0 tree (before P2-09/P2-10) and are recomputed as `N_skills=$(for p in <profile plugins>; do ls plugins/$p/skills; done \| wc -l)`, `N_files=$(find plugins/{core,dev-core,dev-godot,quality-core,infra-github}/skills -type f \| wc -l)`, manifest entries = `N_files + N_skills` | ~6 h | `kit: platforms/tools/sync-project.sh`, `kit: platforms/tools/smoke.sh`, `kit: platforms/tools/INDEX.md`, `kit: platforms/ci/validations/test_sync_project.py`, `kit: README.md`, `kit: docs/design.md`, `kit: docs/projects.md`, `kit: CHANGELOG.md` |
| [`P2-07`](p2-07-format-and-lint-hooks.md) | Format and lint hooks (PostToolUse) for GDScript, Java and spec | kit | P1-07, P2-02 (same `check_kit.py`; P2-02 changes one constant on line 28 and no line count) | ~5 h | `kit:plugins/core/hooks/hooks.json`, `kit:platforms/ci/validations/check_kit.py`, `kit:platforms/ci/validations/hook_post_edit_cases.json`, `kit:platforms/ci/validations/INDEX.md`, `kit:docs/design.md`, `kit:docs/maintenance.md`, `kit:README.md`, `kit:INDEX.md` … |
| [`P2-08`](p2-08-derived-spec-status.md) | Derive task and FEAT status from GitHub instead of editing it by hand | stratics-docs, stratics-client, stratics-server | P1-08 (issue per task is the canonical flow) | ~8 h | `docs: tools/spec-trace/spec_trace.py`, `docs: tools/spec-trace/tests/test_sync_status.py`, `docs: .github/workflows/spec-status-sync.yml`, `docs: .github/spec-sync-pr-body.md`, `docs: .github/workflows/docs-checks.yml`, `docs: docs/spec/spec.md`, `docs: docs/spec/features/FEAT-*.md`, `docs: docs/spec/traceability.md` … |
| [`P2-09`](p2-09-consolidate-skills.md) | Consolidate overlapping skills (code-standards, architecture, session) | kit (agent-rules-kit) | P2-03 (the two `plugins/core/AGENTS.md` pointer lines are edited after P2-03 has reordered the file), P2-02 (rule bodies and the root `INDEX.md` Loads cells; this prompt then only swaps the skill name inside them) | ~4 h | `kit:plugins/dev-core/skills/code-standards/SKILL.md`, `kit:plugins/dev-core/skills/code-standards/references/yagni-ladder.md`, `kit:plugins/architect-core/skills/architecture/SKILL.md`, `kit:plugins/architect-core/skills/architecture/references/pattern-catalog.md`, `kit:plugins/core/skills/session/SKILL.md`, `kit:plugins/core/skills/session/references/kit-proposal.md`, `kit:plugins/core/skills/session/references/handoff-record.md`, `kit:plugins/dev-core/skills/clean-code/SKILL.md` … |
| [`P2-10`](p2-10-extras-plugin.md) | Move non-core skills to an optional extras plugin | kit (agent-rules-kit) | P2-09 (it rewrites `plugins/core/INDEX.md`, `plugins/dev-core/INDEX.md` and root `INDEX.md:24`; apply this prompt on top of its result so the two edits do not collide), P2-07 (same `check_kit.py`; P2-07 adds imports and blocks above and below the lines edited here) | ~3 h | `kit: plugins/extras/INDEX.md`, `kit: plugins/extras/plugin.json`, `kit: plugins/extras/.devin-plugin/plugin.json`, `kit: plugins/extras/.claude-plugin/plugin.json`, `kit: plugins/extras/skills/find-skills/ (moved from plugins/core/skills/find-skills)`, `kit: plugins/extras/skills/skill-creator/ (moved from plugins/core/skills/skill-creator)`, `kit: plugins/extras/skills/frontend-design/ (moved from plugins/dev-core/skills/frontend-design)`, `kit: plugins/extras/skills/krita/ (moved from plugins/dev-godot/skills/krita)` … |
| [`P2-11`](p2-11-tokens-skill-simplify.md) | Simplify the tokens skill (drop compression levels) | kit (agent-rules-kit) | none | ~0.5 h | `kit:plugins/core/skills/tokens/SKILL.md`, `kit:CHANGELOG.md`, `kit:plugins/core/INDEX.md` |
| [`P2-12`](p2-12-java-facts-update.md) | Update Java and Spring facts (Java 25, Spring Boot 4.1.x) | kit (agent-rules-kit) | P2-01 | ~2 h | `kit: plugins/dev-java/templates/project-agents-java-spring.md`, `kit: platforms/kits/java-maven/pom-parent.xml`, `kit: platforms/kits/java-maven/README.md`, `kit: plugins/dev-java/skills/java-standards/references/java-25-lts.md`, `kit: plugins/dev-java/skills/java-standards/references/build-and-dependencies.md`, `kit: plugins/dev-java/skills/java-standards/SKILL.md`, `kit: CHANGELOG.md` |
| [`P2-13`](p2-13-java-references-jdbcclient-archunit.md) | Java references: JdbcClient plus Flyway pattern and ArchUnit rules | kit (agent-rules-kit); stratics-server (read-only input) | P2-12 | ~2 h | `kit: plugins/dev-java/skills/java-standards/references/jdbcclient-flyway.md`, `kit: plugins/dev-java/skills/java-standards/references/archunit-rules.md`, `kit: plugins/dev-java/skills/java-standards/SKILL.md`, `kit: CHANGELOG.md` |
| [`P2-14`](p2-14-testcontainers-offline-fast.md) | Testcontainers, offline Maven and fast profile guidance | kit (agent-rules-kit), stratics-server | P2-12, P2-13 (same `SKILL.md`; P2-13 inserts its reference line first so the three reference lines stay together) | ~3 h | `kit: plugins/dev-java/skills/java-standards/references/build-and-dependencies.md`, `kit: plugins/dev-java/skills/java-standards/references/testcontainers.md`, `kit: plugins/dev-java/skills/java-standards/SKILL.md`, `kit: CHANGELOG.md`, `server: AGENTS.md`, `server: pom.xml` |
| [`P2-15`](p2-15-apply-sync-to-stratics-repos.md) | Apply the generated agent configuration to the three Stratics repos | stratics-docs, stratics-client, stratics-server (plus one small fix in the kit) | P2-04, P2-05, P2-06 merged to kit main; P1-02 merged in stratics-docs (same `AGENTS.md`); P2-08 merged in stratics-docs (same `.github/workflows/docs-checks.yml`); P1-06 merged in the kit for step 7 | ~8 h | `kit: platforms/tools/sync-project.sh`, `kit: platforms/tools/doctor.sh`, `kit: platforms/tools/smoke.sh`, `kit: README.md`, `kit: CHANGELOG.md`, `docs: CLAUDE.md`, `docs: .claude/settings.json`, `docs: .claude/rules/architect-sdd-spec.md` … |

### Phase 3

| Prompt | Title | Repos | Depends on | Effort | Files touched |
|---|---|---|---|---|---|
| [`P3-01`](p3-01-godot-netplay-references.md) | Godot online 2D references (authority, codec, testable logic, pitfalls, generated files, performance) | kit | P1-04, P1-05, P1-06 | ~6 h | `kit: plugins/dev-godot/skills/godot-standards/references/authority-and-prediction.md`, `kit: plugins/dev-godot/skills/godot-standards/references/network-codec.md`, `kit: plugins/dev-godot/skills/godot-standards/references/testable-game-logic.md`, `kit: plugins/dev-godot/skills/godot-standards/references/gdscript-4-pitfalls.md`, `kit: plugins/dev-godot/skills/godot-standards/references/scenes-and-generated-files.md`, `kit: plugins/dev-godot/skills/godot-standards/references/performance-budget.md`, `kit: plugins/dev-godot/skills/godot-standards/SKILL.md`, `kit: CHANGELOG.md` |
| [`P3-02`](p3-02-gdtoolkit-ci-and-hook.md) | gdtoolkit lint and format in the Godot CI kit and in stratics-client | kit, stratics-client, stratics-docs | P1-05 (which itself follows P1-06, so the `ci-godot.yml` order is P1-06, P1-05, P3-02), P3-01 (same `godot-standards/SKILL.md` and `gdscript-4-pitfalls.md`; P3-01 first, so the godot-guard line lands once) | ~4 h | `kit: platforms/kits/godot/gdlintrc`, `kit: platforms/kits/godot/requirements-gdtoolkit.txt`, `kit: platforms/kits/godot/README.md`, `kit: platforms/kits/github/workflows/ci-godot.yml`, `kit: platforms/kits/github/README.md`, `kit: plugins/dev-godot/skills/godot-standards/SKILL.md`, `kit: plugins/dev-godot/skills/godot-standards/references/gdscript-4-pitfalls.md`, `kit: CHANGELOG.md` … |
| [`P3-03`](p3-03-devin-environment-and-playbooks.md) | Devin environment.yaml templates and playbooks | kit, stratics-docs, stratics-client, stratics-server | P2-02 and P2-03 (rules and `plugins/core/AGENTS.md` carry the critical constraints a Devin Cloud child receives), P2-14 (offline Maven: `dependency:go-offline` must work on stratics-server before the maintenance step can rely on it), P3-02 (the Godot environment installs its gdtoolkit pin) | ~6 h | `kit: platforms/kits/devin/README.md`, `kit: platforms/kits/devin/environment.godot.yaml`, `kit: platforms/kits/devin/environment.java.yaml`, `kit: platforms/kits/devin/environment.docs.yaml`, `kit: platforms/kits/devin/snapshot-checklist.md`, `kit: platforms/kits/devin/playbooks/implement-issue.devin.md`, `kit: platforms/kits/devin/playbooks/fix-round.devin.md`, `kit: platforms/kits/devin/playbooks/devin-review-autofix.md` … |
| [`P3-04`](p3-04-spec-regimes.md) | Two spec regimes: spec-anchored contracts, spec-first features | kit (agent-rules-kit), stratics-docs | P3-06 (same `sdd-process.md`; P3-06 renumbers its step table first), P2-08 (stratics-docs steps 6-9 only; kit steps 1-5 may run before it) | ~3 h | `kit: plugins/architect-sdd/skills/sdd-constitution/references/sdd-process.md`, `kit: plugins/architect-sdd/skills/sdd-constitution/SKILL.md`, `kit: plugins/architect-sdd/templates/spec-index.md`, `kit: plugins/architect-sdd/templates/spec-feature.md`, `kit: CHANGELOG.md`, `docs: docs/spec/spec.md`, `docs: docs/spec/decisions/DPRO-014-spec-regimes.md (only if the owner asks for a decision)`, `docs: changelog.d/p3-04-spec-regimes.changed.md` |
| [`P3-05`](p3-05-sdd-spike-lane.md) | sdd-spike: a prototype lane for game feel | kit | P3-06 (step-table renumbering of `sdd-process.md` and the `plugins/architect-sdd/INDEX.md` rows), P3-04 (entry-point rewrite of the same `sdd-process.md` sentence); this prompt touches `sdd-process.md` only in the entry-point sentence and never a step number | ~3 h | `kit: plugins/architect-sdd/skills/sdd-spike/SKILL.md`, `kit: plugins/architect-sdd/skills/sdd-spike/agents/openai.yaml`, `kit: plugins/architect-sdd/templates/doc-spike-report.md`, `kit: plugins/architect-sdd/INDEX.md`, `kit: plugins/architect-sdd/skills/sdd-constitution/references/sdd-process.md`, `kit: plugins/infra-github/skills/branching-and-versioning/SKILL.md`, `kit: CHANGELOG.md` |
| [`P3-06`](p3-06-merge-analyze-audit.md) | Merge sdd-analyze and sdd-audit into one mechanical check | kit (agent-rules-kit) | P1-08 | ~3 h | `kit:plugins/architect-sdd/skills/sdd-check/SKILL.md`, `kit:plugins/architect-sdd/skills/sdd-check/references/check-list.md`, `kit:plugins/architect-sdd/skills/sdd-analyze/SKILL.md`, `kit:plugins/architect-sdd/skills/sdd-audit/SKILL.md`, `kit:plugins/architect-sdd/INDEX.md`, `kit:plugins/architect-sdd/skills/sdd-clarify/SKILL.md`, `kit:plugins/architect-sdd/skills/sdd-plan/SKILL.md`, `kit:plugins/architect-sdd/skills/sdd-tasks/SKILL.md` … |
| [`P3-07`](p3-07-verification-gates-and-worktree-cleanup.md) | Verification gates in sdd-implement and worktree cleanup in reviewer | kit | P3-06 (same `sdd-implement/SKILL.md`; it only changes that file's `SDD step N` description and H1), P1-08 (P1-08 replaces §1, §4 and the commit step of §2 of `sdd-implement`; it keeps the sentence `Run the task's proof literally and summarize output in History.` verbatim, which is this prompt's only anchor, never a step number). Execute before P3-11 (it inserts two lines into §3 of `validate-implementation`) | ~2 h | `kit:plugins/architect-sdd/skills/sdd-implement/SKILL.md`, `kit:plugins/quality-core/agents/reviewer.md`, `kit:plugins/quality-core/skills/validate-implementation/SKILL.md`, `kit:CHANGELOG.md` |
| [`P3-08`](p3-08-process-loop-plugin.md) | process-loop plugin from the DPRO-011 review loop | kit (agent-rules-kit), stratics-docs | P1-08 (task template and issue-per-task flow the loop assumes), P2-10 (plugin registration pattern and the decision on what `all` bundles), P2-09 (description budget: 6,803 today + 511 new = 7,314 > 7,200; about 6,210 after P2-09, so about 6,721 once the four new descriptions are added) | ~8 h | `kit: plugins/process-loop/plugin.json`, `kit: plugins/process-loop/.claude-plugin/plugin.json`, `kit: plugins/process-loop/.devin-plugin/plugin.json`, `kit: plugins/process-loop/INDEX.md`, `kit: plugins/process-loop/skills/loop-orchestrate/SKILL.md`, `kit: plugins/process-loop/skills/loop-orchestrate/agents/openai.yaml`, `kit: plugins/process-loop/skills/loop-orchestrate/references/waiter-events.md`, `kit: plugins/process-loop/skills/loop-review/SKILL.md` … |
| [`P3-09`](p3-09-evals-and-kpis.md) | Skill evals with claude plugin eval and a KPI tool over the review ledger | kit | P2-09, P3-06 (final skill names; both keep `godot-standards`, `java-standards`, `sdd-tasks`, `validate-implementation`, `protocol-contract`, `investigate`, `skeptic` and the `reviewer` agent, and P3-06 renames the `sdd-analyze` that `sdd-tasks` §4 cites to `sdd-check`); phase 1 must be merged, because two cases grade the P1-06 boot proof and P1-03 confidence wording; P2-07 and P2-10 (same `check_kit.py`), P3-05 (same `plugins/architect-sdd/INDEX.md`) | ~8 h | `kit:platforms/ci/validations/check_kit.py`, `kit:.gitignore`, `kit:plugins/dev-godot/evals/`, `kit:plugins/dev-java/evals/`, `kit:plugins/architect-sdd/evals/`, `kit:plugins/quality-core/evals/`, `kit:plugins/architect-core/evals/`, `kit:plugins/dev-core/evals/` … |
| [`P3-10`](p3-10-progress-json-harness.md) | progress.json harness for long implementations | kit | P1-08 (issue per task, ten-column rows; it rewrites `sdd-tasks` and `sdd-implement`, so anchor on sentences, never on step numbers), P2-08 (derived status is the post-merge source of truth this prompt defers to), P2-15 (same `sync-project.sh`; its kit step is the last earlier edit), P3-04, P3-06 and P3-07 (same `sdd-process.md`, `sdd-tasks` and `sdd-implement` files; run them first) | ~4 h | `kit: platforms/ci/schemas/progress.schema.json`, `kit: platforms/kits/sdd/progress.example.json`, `kit: platforms/ci/validations/check_spec.py`, `kit: platforms/ci/validations/test_check_spec.py`, `kit: platforms/tools/sync-project.sh`, `kit: platforms/ci/schemas/INDEX.md`, `kit: platforms/ci/README.md`, `kit: platforms/ci/validations/INDEX.md` … |
| [`P3-11`](p3-11-review-md-and-code-review.md) | REVIEW.md template and /code-review in validate-implementation | kit | P3-07 (it adds one bullet to `validate-implementation` §2, so §3 of that file shifts by one line; this prompt anchors on sentences, never on a line number inside that file) | ~2 h | `kit: platforms/kits/github/REVIEW.md`, `kit: platforms/kits/github/README.md`, `kit: platforms/kits/INDEX.md`, `kit: docs/projects.md`, `kit: plugins/quality-core/skills/validate-implementation/SKILL.md`, `kit: CHANGELOG.md` |

## Files

- `p1-01-freeze-layout-and-path-gate.md`
- `p1-02-fix-stale-kit-paths-in-stratics-docs.md`
- `p1-03-resolve-confidence-rule.md`
- `p1-04-godot-movement-model-not-default.md`
- `p1-05-godot-tests-gdunit4-never-skip.md`
- `p1-06-godot-boot-proof.md`
- `p1-07-hook-guard-coverage.md`
- `p1-08-sdd-absorb-architect-deltas.md`
- `p2-01-remove-machine-facts.md`
- `p2-02-path-rules-with-content.md`
- `p2-03-agents-md-order-and-lines.md`
- `p2-04-sync-project-claude-md-and-settings.md`
- `p2-05-sync-project-rules.md`
- `p2-06-sync-project-vendored-skills.md`
- `p2-07-format-and-lint-hooks.md`
- `p2-08-derived-spec-status.md`
- `p2-09-consolidate-skills.md`
- `p2-10-extras-plugin.md`
- `p2-11-tokens-skill-simplify.md`
- `p2-12-java-facts-update.md`
- `p2-13-java-references-jdbcclient-archunit.md`
- `p2-14-testcontainers-offline-fast.md`
- `p2-15-apply-sync-to-stratics-repos.md`
- `p3-01-godot-netplay-references.md`
- `p3-02-gdtoolkit-ci-and-hook.md`
- `p3-03-devin-environment-and-playbooks.md`
- `p3-04-spec-regimes.md`
- `p3-05-sdd-spike-lane.md`
- `p3-06-merge-analyze-audit.md`
- `p3-07-verification-gates-and-worktree-cleanup.md`
- `p3-08-process-loop-plugin.md`
- `p3-09-evals-and-kpis.md`
- `p3-10-progress-json-harness.md`
- `p3-11-review-md-and-code-review.md`
