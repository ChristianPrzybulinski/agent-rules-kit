# Changelog

Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/). Versioning: [SemVer](https://semver.org/).

## [Unreleased]

### Added
- `docs/features/`: one `KIT-NNN` file per kit improvement the owner confirmed (template, process, index), each with a `kit-feature` issue; the implementing PR closes the issue and its CHANGELOG line cites `KIT-NNN`. KIT-001 records #68 retroactively (issue #69). Why: improvements proposed in project sessions (Stratics night run 2026-10-07) had no history in the kit; the kit stays out of the project's review loop and is implemented by hand. Owner decision 2026-10-07 (chat). `docs/maintenance.md` gains the "kit feature" row.
- `LICENSE`: proprietary, all rights reserved (no copying, redistribution or model training without written permission; a contribution grant to the copyright holder); the vendored third-party skills keep their MIT and Apache-2.0 licenses. `SECURITY.md`: private reporting, supported versions (latest release and `main`) and scope. Owner request 2026-10-06.

### Changed
- KIT-006: `check_spec.py` fails on a merge-conflict marker (`<<<<<<<`, `|||||||`, `>>>>>>>` at a line start) left in any Markdown file under the spec dir. Why: on 2026-10-07 a Stratics spec PR pushed a FEAT with its conflict markers in `## History`, and every spec gate passed on that head.
- KIT-005: `validate-implementation` § 3: gates run in a complete checkout; a gate that stops on a missing path in a sparse or partial worktree is a failed run, and under `set -e` it skips every later gate. Why: on 2026-10-07 `dev.sh lint` in a sparse stratics-docs worktree exited 2 at its third step and never reached the `doc-structure` check, which two reviewed PRs had turned red on `main` (stratics-docs#607, #610). Owner confirmed in chat.
- KIT-002: `sync-project.sh --vendor-skills` no longer copies the `core` plugin's skills: a vendored project keeps `core@ai-kit` enabled (the guard hook lives there), so its skills load from the plugin, and the copies made `collab-two-humans`, `parallelize`, `session` and `tokens` load twice in every session inside the repository (the three Stratics repositories, 2026-10-07). A resync removes the marked copies. Tests and smoke follow.
- KIT-001: `plugins/core/AGENTS.md` § Truth: a failure is "pre-existing" only after the same command failed, in the session, on the commit before the first change (for a PR: its base); a mid-series `main` is no baseline. Why: on 2026-10-07 a Stratics architect session called a red `dat-importer` test pre-existing because it compared against a `main` that already held its own earlier PRs of the same series (DPRO-015 P2/P5/P6 had edited a file whose sha256 seven provenance rows pin); the regression shipped and needed a fix PR (stratics-docs#580). Owner approved the proposal in chat.
- `evals.yml` runs only on `workflow_dispatch`. The weekly schedule is removed: the `ANTHROPIC_API_KEY` secret is not set (owner decision 2026-10-06), so each Monday run would fail and spend Actions minutes.

### Fixed
- KIT-003: `smoke.sh` commits its fixture with `-c maintenance.auto=false -c gc.auto=0`. Git 2.54's commit starts a detached `git maintenance run --auto` that packed the fixture's loose objects while `bootstrap.sh` cloned it, and `smoke: bootstrap failed` came back intermittently (four of four on the owner's clone, 2026-10-07).

## [11.0.0] - 2026-10-06

MAJOR: `sdd-analyze` and `sdd-audit` are removed (merged into `sdd-check`, see Migration), and the default install changes (`extras` leaves `all`; `AI_KIT_USER_RULES` defaults to `0`). The 10.x layout is unchanged: no folder, manifest path or install destination moved.

### Added
- `docs/plans/2026-10-kit-assessment/`: assessment of v10.1.0 against current Anthropic, Cognition and market guidance for the Stratics Godot 2D client + Java server, plus 34 self-contained execution prompts in three phases (freeze layout and fix contradictions; distribute by repository commit and consolidate skills; Godot online 2D references, Devin environment, process-loop plugin, evals and KPIs). Evidence: review-loop first-pass rejection rate 20 of 33 PRs (stratics-docs DPRO-011); 24 of 25 destructive commands pass the hook guard; stale kit paths cited in stratics-docs; FEAT task tables with 128 `todo` rows after ~35 merged PRs.
- `sync-project.sh --check` now scans the project's `*.md` for obsolete kit paths (layouts 1.x to 9.x: `agents/skills/`, `agents/rules/`, `agents/knowledge/`, `rules/godot/`, `rules/java/`, `rules/git/`, `kits/java-maven/`, `kits/github/`, `platforms/install/`, `knowledge/`, `processes/sdd/`, `plugins/ai-kit/`) and fails listing each `file:line`; a historical citation opts out with `<!-- kit-path-ok -->`, and `legacy/`, `docs/sessions/` and `.claude/` are skipped (vendored copies under `.claude/` are verified by their own manifest). Why: consumer specs cite kit paths and every past layout change silently invalidated them (assessment §6 A3) — stratics-docs cited `agents/skills/process/README.md` (`AGENTS.md:20`), `kits/java-maven/pom-parent.xml` and `rules/java/build-and-dependencies.md` (DTEC-001), `rules/godot/godot-2d.md` (DTEC-002), `knowledge/redis/` (DTEC-003), `rules/git/branching-and-versioning.md` (DPRO-001) and `rules/git/git-lfs-and-binaries.md` (DPRO-006); none exist (`ls agents rules knowledge kits processes platforms/install plugins/ai-kit` at the kit root: all absent). Proof: `platforms/ci/validations/test_sync_project.py` exercises the scan on a throwaway repo in 5 unittest cases discovered by the kit's CI.
- `platforms/kits/github/ISSUE_TEMPLATE/task.md` — the canonical task-issue body contract, equal in fields to the project's `task.md` (ten sections: Task, Spec, Repository, Files (owned areas), Proof of completion, DoD, Covers, Depends on, Directive, Notes; `Directive` carries the generic tiers `small | mid | top`, `Complexity`, `Wave`) — plus three `kind: detail` references: `sdd-tasks/references/waves-and-models.md` (wave rules, `Low|Med|High` → tier map, effort in the model picker, worked wave example), `sdd-to-card/references/task-issue.md` (title `[FEAT-nnn Tn]`, kit-section → template-field map, mechanical `Spec`/`DoD`, `status:proposed` → `status:planned`, cross-repo `Closes` line) and `sdd-implement/references/task-pr.md` (executor contract: `Files` scope, allowlisted proof lines, four-step self-check, PR body written outside the worktree, `[BLOCKER]` stop). Why: the issue format, wave rules and model directive lived only in the project (`ops/review-loop`, ARCHITECT.md, CONTRIBUTING.md), so the kit could not speed up a second repository (assessment §4.8, §6 E2). Proof: `grep -c "^## " platforms/kits/github/ISSUE_TEMPLATE/task.md` prints 10 and `diff` of the `^## ` fields against the stratics-docs `task.md` is empty; each reference prints `kind: detail` = 1 and 31/34/38 lines (limit 60).
- `sync-project.sh` now generates two agent-configuration files in the consumer repo, selected by `--profile godot|java|docs` or inferred from `project.godot`/`pom.xml`/`docs/spec/` (first match wins): `CLAUDE.md` — a `generated by agent-rules-kit sync-project.sh v<VERSION>` marker comment plus `@AGENTS.md` — and `.claude/settings.json` — `extraKnownMarketplaces.ai-kit` (github `ChristianPrzybulinski/agent-rules-kit`) plus `enabledPlugins` holding exactly the profile's `@ai-kit` set (godot and docs 5, java 8), with every other key, non-`@ai-kit` entry and key order preserved. A hand-written `CLAUDE.md` without the marker is never overwritten (the run refuses before any write), as are a missing `AGENTS.md` and a malformed `.claude/settings.json`; `init-spec.sh` now requires `AGENTS.md` up front. Why: assessment §4.2 and §6 A1 — the three Stratics repos ship no `CLAUDE.md` or `settings.json`, so a Claude Code web session, the GitHub Action and a collaborator without `bootstrap.sh` ran with no kit rule or plugin; distribution is by commit in the consumer repo. Proof: the `sync-project` block in `platforms/tools/smoke.sh` and the four new `platforms/ci/validations/test_sync_project.py` cases cover inference, idempotence, drift detection and the refusal order.
- dev-java/java-standards: `references/jdbcclient-flyway.md` (JdbcClient without JPA, receipt-based idempotency, injected Clock/RandomGenerator, forward-only Flyway, Testcontainers) and `references/archunit-rules.md` (domain purity, no nondeterminism, inward layers, Spring Modulith alternative), linked from SKILL.md. Evidence: assessment §6 G2; the skill mentioned JPA only while the Stratics server forbids JPA and kept its ArchUnit rule set outside the kit. Proof: check.sh, smoke.sh, unittest and check_kit.py --links green; both references at 53 and 59 lines.
- `sync-project.sh` copies the profile's `plugins/<plugin>/rules/*.md` into `<repo>/.claude/rules/<plugin>-<rule>.md` with a generated marker line (source path, kit version); `--check` reports missing, drifted and stale copies; only marked files are ever removed. `doctor.sh` honours `AI_KIT_USER_RULES=0` to skip user-level rule symlinks so a rule is not loaded twice (default `1` until P2-15). Evidence: assessment §4.2 (cloud sessions and runners load no kit rule) and §6 A1. Proof: smoke cases for idempotence, drift and removal; `check.sh`, `smoke.sh`, unit tests and `check_kit.py --links` green.
- `java-standards`: "Sandboxed agents" section in `references/build-and-dependencies.md` (go-offline snapshot, `./mvnw -o` task runs, `-Pfast` never skips tests, 5-minute budget) and new `references/testcontainers.md` (`@ServiceConnection` container beans, static `@Container` only outside Spring, local reuse, image caching). Evidence: the kit named `-Pfast` once and nothing about offline builds or `@ServiceConnection`; stratics-server had no `fast` profile and PITest bound to `verify` (P2-14, assessment §6 G3).
- `godot-standards`: six online 2D references (`references/authority-and-prediction.md`, `references/network-codec.md`, `references/testable-game-logic.md`, `references/gdscript-4-pitfalls.md`, `references/scenes-and-generated-files.md`, `references/performance-budget.md`) linked from SKILL.md. Evidence: assessment §4.5 and §5.1; before this change no kit line mentioned prediction, move rejection, *.uid or --ignoreHeadlessMode. Proof: `ls plugins/dev-godot/skills/godot-standards/references/ | wc -l` prints 8 and check_kit.py prints `check: OK`, all references at most 60 lines.
- `plugins/core/hooks/hooks.json` gains a `PostToolUse` hook on `Edit`/`Write` (matcher `^(edit|write|Edit|Write)$`, timeout 30) that runs `gdformat` + `gdlint` on `*.gd`, `google-java-format --replace` on `*.java` and the synced `.github/spec-lint/check_spec.py` on `docs/spec/**/*.md` of the edited file, failing open (exit 0 plus a one-line `ai-kit lint: ... not available` notice on stdout) when the tool is absent and reporting the first 2,000 characters of findings on stderr with exit 2 so the agent sees them before the next step; `platforms/ci/validations/hook_post_edit_cases.json` ships 12 deterministic payload/stub-tool cases run by `check_kit.py` against each post-edit command. Why: assessment §6 C2 — a PostToolUse formatter hook is Anthropic's canonical hook example and eliminates the "formatting" review-finding class; the kit had no hook of any kind after an edit. Proof: the manual pipes print `ai-kit lint: gdformat/gdlint not available (pip install gdtoolkit); skipped for x.gd` (`.gd`), silence (`README.md`) and `check_spec.py not available` (`docs/spec/x.md` at the kit root), all `exit=0`; `check_kit.py` reports `12 hook cases` in the summary.
- `sync-project.sh --vendor-skills` copies the profile's `plugins/<plugin>/skills/<name>/` directories whole into `<repo>/.claude/skills/<name>/` with an `.agent-rules-kit` marker and writes `KIT_MANIFEST.json` (kit version, profile, plugin, sha256 per file); in that mode `.claude/settings.json` keeps only `core@ai-kit` for the guard hook; `--check` verifies the manifest and reports drift, missing, extra and stale files; unmarked directories are never touched. Evidence: assessment §4.2 (cloud sessions, runners and Devin Cloud load no kit skill), §5 skills row, §6 A1. Proof: smoke and `test_sync_project.py` cases for idempotence, drift, extra file, profile switch and collision; all four kit gates green.

- `plugins/extras` (requires `core`, not in `all`): `find-skills`, `skill-creator`, `frontend-design`, `krita` and `dbeaver` moved out of the default install with `git mv` (history kept, vendored `VENDOR.md`/`LICENSE.txt` unchanged). Why: assessment §4.7 and §6 F2 — web design, GUI tools for humans, skill discovery by popularity (a prompt-injection vector) and skill authoring do not help an executor implement a task. Proof: description budget unchanged at 6,588 chars; the default install now carries 1,112 chars less; `check.sh`, `smoke.sh`, the unittests and `vendor.sh --check` green.
- Godot CI kit: gdtoolkit 4.5.0 pinned in `platforms/kits/godot/requirements-gdtoolkit.txt`, a default `gdlintrc` (max-line-length 120, max-returns 10, gdlint defaults otherwise) and a `lint` job (`gdformat --check` plus `gdlint`, `addons/` and `.godot/` excluded) in `ci-godot.yml`; `godot-standards` §5 names the command; godot-guard evaluated and not adopted as a gate (2 false positives, 0 true findings on stratics-client). Evidence: stratics-client went from 13 of 18 scripts unformatted and 25 gdlint problems to 0 after the baseline (P3-02, assessment §5.1 and §7 N2).
- `platforms/kits/devin/`: Devin Cloud environment templates (Godot 4.7.2, JDK 25 + Maven, docs; `knowledge` as a list of `name`/`contents` entries, verified on docs.devin.ai on 2026-10-06), snapshot checklist, `implement-issue` and `fix-round` playbooks derived from a project's review-loop child prompts, and the Devin Review autofix note (allowlist `devin-ai-integration[bot]` only, never "All bots"). `docs/design.md` now says Playbooks are kept for Devin Cloud children. Evidence: Devin Cloud loads no plugin hooks or subagents and one skill at a time (assessment §9.2, 2026-10-06); the loop's children ran from hand-pasted prompts outside the kit (P3-03).
- `sdd-spike` (user-only, `agents/openai.yaml` policy) plus `templates/doc-spike-report.md`: a time-boxed `spike/<topic>` lane (two days at most) for game feel with no spec edits and no coverage or lint gate, delivering media, a report and a proposed DGME/DTEC; the `sdd-process.md` entry point names it and `branching-and-versioning` allows `spike/` as the only branch that never merges. Why: assessment §4.6 and §6 E3, a spec written before a character moved on screen (9,451 spec lines, no movement code in stratics-client on 2026-10-06). Proof: `platforms/tools/check.sh` 41 -> 42 skills and 19 -> 20 templates, descriptions within the 7,200-char budget.
- `docs/spec/progress/FEAT-nnn.json`: executor progress file with `passes` per task, written by `sdd-tasks`, updated by `sdd-implement` after the literal proof and read at session start with `git log --oneline -20`; schema `platforms/ci/schemas/progress.schema.json`, example `platforms/kits/sdd/progress.example.json` (FEAT-009 rows), validated by `check_spec.py` (schema, feat exists, file name = feat, unique task ids; structural fallback without jsonschema; +7 tests, 57 in total) and copied by `sync-project.sh` (`SCHEMAS` gains `progress`); `sdd-tasks` section 6, `sdd-implement` orient step and `passes` rule, `sdd-process.md` precedence sentence and layout line, the `session` handoff reference and `doc-session-handoff.md` follow. Why: assessment §5 harness row and §7 N6 (Anthropic, effective harnesses for long-running agents, 2025-11-26: a JSON feature list edited only through `passes`, progress file, commits as checkpoints, git log read at session start; opened 2026-10-06); 128 task rows `todo` and 3 `done` after 27 merged task PRs. After merge the derived status is the source of truth. Proof: 57 unittests OK (also `test_check_spec.py` alone in a venv without jsonschema), `check.sh`, `smoke.sh`, `check_kit.py --links` pass.
- `plugins/process-loop` (skills `loop-orchestrate`, `loop-review`, `loop-child-implement`, `loop-child-fix`; templates `doc-verdict`, `doc-batch-report`; requires `core`, `infra-github`, `quality-core`; in the `all` bundle) and `platforms/kits/review-loop/` (verdict schema, example config without machine paths, the loop-tool decision): the implement-review-merge loop of a running project (DPRO-011) as kit content, so a second project or a second collaborator can start it from kit files plus the project's loop tool. Registered in the Devin, Claude and Codex catalogs; the plugin count is now fourteen (thirteen in `all`). Why: assessment §4.8 and §7 N4; 20 of 33 PRs were flagged on the first pass by these review rules (stratics-docs DPRO-011 amendment 2026-10-05), and the orchestrator prompt and config held absolute paths, so no second project could run it. Proof: `platforms/tools/check.sh`, `smoke.sh` (14 plugins), the unittests and `check_kit.py --links` pass; descriptions total within the 7,200-char budget.
- `platforms/kits/github/REVIEW.md`: the five review criteria (scope, correctness, architecture, security, docs) in the repository-root form hosted Claude Code Review reads, de-projected from `doc-review-checklist.md` (no coverage numbers, contract fields or FEAT status), with "flag only gaps that affect correctness or the stated criteria; nits are optional"; `validate-implementation` §3 runs `/code-review` as a background subagent in Claude Code before the verdict and folds confirmed findings into the criterion table. Evidence: `grep -rc code-review plugins/quality-core/` printed 0 on 2026-10-06; no Stratics repository had a `REVIEW.md`; assessment §5 verification row and §7 N7; the hosted-review and local-command facts were checked at code.claude.com/docs/en/code-review on 2026-10-06. Proof: `check.sh`, `smoke.sh`, the unittests and `check_kit.py --links` pass.
- Evals and KPIs (assessment N5): 24 `claude plugin eval` cases under `plugins/<p>/evals/` for godot-standards, java-standards, sdd-tasks, validate-implementation (with the reviewer profile), protocol-contract, investigate and skeptic, drawn from the 10.1.0 and batch-20261004 review failures (a claimed proof never re-run, a proof that passes on zero tests, `--quit` exit 0 after a `SCRIPT ERROR`, a Files cell without a test path, a field owned by another feature); `check_kit.py` admits `evals/` at the plugin root and rejects a case without `prompt.md`/`case.yaml` or without `graders/*.md`; `.github/workflows/evals.yml` runs them weekly and on demand with a pinned model and judge; `platforms/tools/kpi.py` prints first-pass approval, rounds per PR, spec-owned findings and median time to green per batch from `ledger.csv` (unit test `test_kpi.py`, 5 tests). Evidence: no eval existed; 20 of 33 PRs flagged on the first pass (DPRO-011); targets (first-pass approval >= 60%, spec-owned findings <= 25%) and the before/after rule are in `docs/maintenance.md`.

### Changed
- `sync-project.sh` copies `.github/spec-lint/`, its README and the kit workflow only when the project has `docs/spec` (it prints `sync: no docs/spec, spec-lint skipped` otherwise, and `--check` skips the validator checks there); an existing workflow that runs `check_spec.py` (stratics-docs `docs-checks.yml`) keeps counting. `doctor.sh` defaults `AI_KIT_USER_RULES` to `0` because the consumer repos now carry `.claude/rules`; `1` restores the user-level rule symlinks. Why: P2-15 applies the sync to stratics-client and stratics-server, which have no `docs/spec` (assessment §4.2, §6 A1). Proof: new smoke case for a repo without `docs/spec`; `sync-project.sh --check` on stratics-client and stratics-server no longer reports `check_spec.py missing`.
- `check_kit.py` `OPTIONAL_PLUGINS = {"extras"}`: the "'all' requires every content plugin" rule exempts opt-in plugins, and a name in the set that is not a plugin directory fails; `skills.lock` plugin column is `extras` for `skill-creator`, `find-skills` and `frontend-design`; `smoke.sh` expects 13 plugin directories; `core`, `infra-persistence` and `all` descriptions no longer name the moved skills (assessment §6 F2).
- The 10.x layout is declared frozen until at least 2027-01-01: new "Layout stability" principle in `docs/design.md`; `docs/maintenance.md` now classifies content changes (MINOR adds a rule, skill, reference, template, validator gate or document; PATCH corrects one without changing routing); the PR template replaces the dead `LAYOUT_VERSION` checkbox with a no-layout-change check. `docs/projects.md` no longer cites `platforms/install/` (removed in 8.0, `## [8.0.0]` `### Removed`) or describes a separate "knowledge" tree (folded into references in 8.0): content reaches the agent through the plugin marketplaces or `bootstrap.sh`. Why: layout changes in 4.0, 6.0, 8.0, 9.0 and 10.0 each forced `bootstrap`/`doctor` re-runs and invalidated consumer citations, so paths are now a contract (assessment §4.1, §6 A3). Proof: `grep -n 'platforms/install\|knowledge' docs/projects.md` prints nothing and `grep -c 'LAYOUT_VERSION' .github/PULL_REQUEST_TEMPLATE.md` prints 0.
- `godot-standards` section 3, the `project-agents-godot-2d.md` template and `editor_settings_hints.md` no longer prescribe `_physics_process` + `move_and_slide()`; the movement model is declared per project in `AGENTS.md` (option A physics bodies, option B grid/tile-step with a server-authoritative position, prediction of at most one step and tween/lerp presentation in `_process`), never mixed in one entity (assessment §4.4, §6 D1; stratics-docs DGME-002; stratics-client `AGENTS.md:41`). Proof: `grep -rn 'Move a body' plugins/` prints nothing, `SKILL.md` shows 2 `Option A`/`Option B` lines, and `wc -l` of `SKILL.md` is 51 (limit 80).
- `plugins/core/AGENTS.md` section Skepticism rewritten as verifiable rules (an unsourced claim is tagged `[HYPOTHESIS]`; unblocked ambiguity -> decide and state the assumption in one line; a real blocker -> one question with 2-4 options and a recommendation), the numeric 98% confidence threshold removed from the global rules and from the `skeptic` policy and description, and the duplicate ambiguity lines in Work loop and Communication folded into Skepticism. Evidence: `AGENTS.md:15` ("Confidence < 98% -> do not proceed") contradicted `AGENTS.md:29` ("Ambiguous but unblocked -> decide, state the assumption, proceed"), so the agent picked one at random (assessment §4.4, item B1). Proof: `grep -n '98' plugins/core/AGENTS.md plugins/quality-core/skills/skeptic/SKILL.md plugins/quality-core/INDEX.md` prints nothing, `grep -c 'Ambigu' plugins/core/AGENTS.md` prints 1 and the file stays at 57 lines (limit 60).
- Godot boot proof in `godot-standards` §5, `reviewer` step 3, `validate-implementation` §3, the `project-agents-godot-2d.md` template and `ci-godot.yml` is now `godot --headless --path . --import` followed by `! godot --headless --path . --quit 2>&1 | grep -Eq 'SCRIPT ERROR|Parser Error'` (in CI the `--quit` line tees `boot.log` and the grep is the step's last line), because `--quit` exits 0 after a script error and skips the import scan (assessment §4.4, §6 D3; stratics-docs ARCHITECT.md delta 6, 2026-10-05; stratics-docs#84). Proof: `grep -rn -- '--headless --quit' plugins platforms` prints nothing, every remaining `--headless --path . --quit` is the grep form or the `tee boot.log` line, and the broken-case run is in the PR body.
- PreToolUse guard (`plugins/core/hooks/hooks.json`): 5 to 22 blocked command classes (rm -r -f and --recursive --force, find -delete, push +ref/:ref/--delete, branch -D, checkout -- / restore, stash drop|clear, filter-repo, lfs migrate, compose down -v, docker prune, flyway clean, destructive SQL files, terraform destroy, gh repo delete, truncate -s 0, chmod -R 777, curl | sh); emits the current contract `hookSpecificOutput.permissionDecision="deny"` (exit 2 kept; the embedded Python needs 3.6 or newer for the `(?-i:...)` groups); case table 13/13 to 52/44; `docs/design.md` now lists covered and uncovered operations. Why: 21 of the 22 commands listed in the assessment §4.3 table plus `truncate -s 0 file` passed the previous guard. Proof: `python3 -c "import json;d=json.load(open('platforms/ci/validations/hook_guard_cases.json'));print(len(d['blocked']),len(d['allowed']))"` prints `52 44`, the assessment §9.1 loop over the 21 commands prints `BLOCKED` 21 times, `platforms/tools/check.sh` prints `check: OK (12 plugins, 46 skills, 3 rules, 19 templates, 20 indexes, 85 links)` and `platforms/tools/smoke.sh` ends `smoke: OK (46 skills, app fallback, cleanup, symlink safety, manifests)`.
- `ci-godot.yml` runs gdUnit4 by default or GUT as the alternative, fails when no runner exists or zero tests execute, and uploads `reports/` plus the runner log as the `godot-test-reports` artifact (`if: always()`); `testing` adds the GDScript policy (no percentage gate; every game rule in a pure `RefCounted` class with scene-free tests; scene tests are integration only); `godot-standards`, `project-agents-godot-2d.md` and both kit READMEs name gdUnit4 first, and the godot `.gitignore` ignores `reports/` (assessment §4.4, §6 D2; `reviewer.md:21`; stratics-docs DTEC-010). Proof: `grep -c 'skipping tests' platforms/kits/github/workflows/ci-godot.yml` prints 0 and `grep -c 'upload-artifact@v7'` prints 1 (the export job moved to the caller in kit#28); the broken-case run is in the PR body.
- `sdd-tasks`/`sdd-to-card`/`sdd-implement`: one issue per task row (`[FEAT-nnn Tn]`), ten-column task rows with `Complexity | Model | Wave` (`templates/spec-feature.md` too), generic model tiers, worktree and PR per issue with cross-repo `Closes`, and the kit issue template `platforms/kits/github/ISSUE_TEMPLATE/task.md`; absorbs stratics-docs ARCHITECT.md deltas 1-5 (assessment §4.6, §6 E2). `sdd-tasks` §5 gains the three missing cut checks (generated/build files join `Files`, named value domains and public identifiers, no refused words in proofs) and §3 the wave rule; `sdd-to-card` fills the template verbatim with `Spec`/`DoD` mechanical, cuts in wave order into one backlog repo and keeps `card` for the optional FEAT card alone (task state derives from GitHub, P2-08); `sdd-implement` starts one worktree per issue (`git worktree add`, branch `feature/FEAT-nnn-Tn-<slug>`), requires a clean `git status --porcelain` before the PR and leaves merge to the architect's FEAT/REQ/DEC review; `sdd-process.md` states the per-issue loop and drops the kit#32 "Variant" section, which this entry promotes to the default flow. Proof: `grep -c "git worktree add"`, `grep -c "git status --porcelain"` and `grep -c "feature/FEAT-nnn-slug"` on `sdd-implement/SKILL.md` print 1, 1, 0; `grep -c "to-card\` after \`tasks\`" sdd-process.md` prints 1; `platforms/tools/check.sh` prints `check: OK (12 plugins, 46 skills, 3 rules, 19 templates, 20 indexes, 85 links)` and `platforms/tools/smoke.sh` prints `smoke: OK (46 skills, app fallback, cleanup, symlink safety, manifests)`.
- Machine-specific facts removed from the remaining kit references and docs: `java-25-lts.md` and `compose-v2-vs-v5.md` now point to the project pins (`.java-version`, `pom.xml`, `~/.m2/toolchains.xml`, `actions/setup-java` Temurin, the `maven:3.9-eclipse-temurin-25`/`eclipse-temurin:25-jre` images, the Compose v2+ requirement) instead of recording what is installed on the kit owner's machine; the docker `SKILL.md` reads "the Compose v2+ CLI behavior"; `toolchains.xml.example` ships a placeholder `jdkHome` with the common macOS/Linux layouts in an XML comment; `docs/projects.md` no longer cites the owner's home directory as the real example. `godot-4-versions.md` points to the project pin (`project.godot` `config/features` and the project `AGENTS.md`) instead of a kit-pinned version, and to the `barichello/godot-ci:<project version>` image whose tag must be checked on Docker Hub before a bump; `docs/maintenance.md` was already free of machine facts (the `docs/machine.local.md` pointer, kit#28) and is unchanged. Evidence: the machine-facts grep over `plugins`, `docs` and `platforms/kits` (excluding `docs/plans`) went from 5 lines to 3, all inside the sanctioned `docs/machine.local.md.example` template and the `docs/INDEX.md` row describing it — 0 elsewhere; the `/opt/homebrew` grep over `plugins`, `docs` and `platforms` prints 3 lines (the launchd plist PATH, the example-path XML comment in `toolchains.xml.example`, and the sanctioned `docs/machine.local.md.example`) with the real `jdkHome` element now a placeholder (P2-01, assessment §4.2 and §6 A2).
- Path-scoped rules (`godot.md`, `java.md`, `spec.md`) carry 8-12 inline always/never constraints and one pointer to the owning skill; `RULE_BODY_MAX_LINES` 12 to 40. Evidence: assessment §6 B2 and §7 N3; a Devin Cloud child receives only `AGENTS.md` and glob rules, and the three bodies were two pointer lines each. Proof: `check.sh`, `smoke.sh`, unit tests and `check_kit.py --links` green.
- `sync-project.sh --check` now also verifies `CLAUDE.md` (marker carrying the kit's current `VERSION`, `@AGENTS.md` as the only non-comment line) and `.claude/settings.json` (`extraKnownMarketplaces.ai-kit` equal to the kit object, the `@ai-kit` keys of `enabledPlugins` equal to the profile set with every value `true`), failing with `diverges for profile <name>`; usage is now `sync-project.sh [--check] [--profile godot|java|docs] [--workflow <file>] <repo-dir>`, and the generated `spec-lint/README.md` states the plugin-loading limits (local sessions after folder trust, CI only with `hasTrustDialogAccepted`, never cloud sessions).
- plugins/core/AGENTS.md: sections reordered to Boundaries, Session, Work loop, Craft, Security, Communication, Truth, Skepticism (concrete rules first; IFScale arXiv:2507.11538 primacy bias, assessment §5.1 and §6 B3) and two lines added: task scope = the issue's Files cell, a change outside it stops and names the path (lifted from stratics-docs CONTRIBUTING.md, the rule that saved the most review rounds); when compacting, preserve modified files and test commands (Claude Code compaction guidance). No existing line changed: sorted diff against main shows 2 added, 0 removed; 59 lines (limit 60) (P2-03).
- Java and Spring facts updated to Java 25 LTS + Spring Boot 4.1.x: the project-agents-java-spring template fixes Java 25 and Boot [4.1.x] and declares persistence (JdbcClient + Flyway without JPA, or JPA) and the error format (RFC 9457 ProblemDetail, or a project error catalog) as project choices; pom-parent.xml imports the 4.1.1 BOM (3.5.x left OSS support on 2026-06-30) with plugin versions from a working Boot 4.1.1 build and a Tomcat-override note for the dependency-check gate; java-25-lts.md carries the dated Boot facts with spring.io sources; ci-java.yml already ran Temurin 25. Evidence: grep for '3.5.16|Spring Boot [3|Java [21]|RFC 7807' over plugins, platforms and docs went from 3 lines to 0 (P2-12, assessment §4.4, §6 G1, §9.2; stratics-docs DTEC-009).
- Skills consolidated 46 -> 42 (model-invocable 33 -> 30, descriptions 7,181 -> 6,588 of 7,200): `clean-code` + `simplicity` -> `code-standards` (dev-core), `clean-architecture` + `ddd-and-patterns` -> `architecture` (architect-core), `sessions` + `session-review` + `session-handoff` -> `session` (core, `/session start | review | handoff <topic>`; the handoff record is written only on explicit request, the skill is model-invocable so Codex policy and `disable-model-invocation` are dropped per the parity gate). Tables and procedures moved to `references/`. Why: the merged pairs named each other as "Not for" neighbours and Devin Cloud loads one skill at a time (assessment §4.7, §6 F1). Proof: old-name grep empty outside CHANGELOG and docs/plans; check.sh, smoke.sh, unittest and --links green. Migration (user-invoked names): see table below (P2-09).
  - clean-code -> code-standards
  - simplicity -> code-standards
  - clean-architecture -> architecture
  - ddd-and-patterns -> architecture
  - sessions -> session start
  - session-review -> session review
  - session-handoff -> session handoff <topic>
- tokens skill: the lite/full/ultra compression levels and the "keep the chosen level for the session" rule are removed; §1 now states that a register sets density, never language or format. Output compression does not reduce input tokens, where the cost is, and a session-wide level contradicted the pt-BR conversation rule (AGENTS.md) and "do not compress" for governed documents in the same skill (assessment §4.7, §6 F3). Proof: grep -rnw -e ultra -e lite plugins prints nothing; SKILL.md 51 -> 50 lines; description and INDEX.md row unchanged; all four kit gates green (P2-11).
- `check_kit.py` accepts `PostToolUse` hook events (matcher must `re.fullmatch` `Edit` and `Write`, `type: command`, timeout at most 30; the PreToolUse guard keeps its 10 s ceiling) and runs `hook_post_edit_cases.json` in a throwaway repo per case with stub tools first on `PATH` and a `python3` symlink to the real interpreter. `docs/design.md` gains the "Formatting runs in a hook, not in instructions" principle, `docs/maintenance.md` extends the fail-open statement to the new hook, and the README platform table and root INDEX row name it. Proof: negative runs fail with `timeout must be at most 30` (timeout 31) and `matcher must match Edit and Write` (matcher `^Edit$`); `grep -c 'PostToolUse' platforms/ci/validations/check_kit.py` prints 8 (P2-07).
- The `docs/design.md` copy principle is now "zero content copies on the machine, one versioned copy per repository" (skills join path rules and spec validators as allowed generated copies), a second `.agents/skills` copy is recorded as left out because Devin also scans `.claude/skills`, and `sync-project.sh --check` extends to the vendored manifest: `KIT_VERSION`, profile and skill-set equality, sha256 per listed file, unlisted files in marked directories and generated-but-unlisted skills are all reported, while a `--vendor-skills --check` without a manifest fails pointing at the resync command. Proof: the drift, extra-file and profile-switch cases in `smoke.sh` and `test_sync_project.py`.
- SDD: `sdd-check` (step 3, `researcher` fork, read-only) replaces `sdd-analyze` and `sdd-audit`: the validator verdict plus the consistency table (C1-C10), then the quality checklist (Q1-Q11, `references/check-list.md`), one report with `blocked: yes|no`; the steps are renumbered 0..8 in `sdd-process.md`, every `SDD step N —` description, every `# SDD N —` heading, the plugin index and the FEAT template `## Audit` comment; `sdd-tasks` now cites `sdd-check` row C8 instead of the nonexistent `sdd-analyze` A8. Why: assessment §4.6 and §6 E4, two forked read-only steps of 48 and 50 lines before every plan. Proof: `platforms/tools/check.sh` OK, `smoke.sh` OK, 50 unittests OK, `check_kit.py --links` OK; description budget 6,588 -> 6,445 of 7,200 chars.
- SDD: two spec regimes in `sdd-process.md` (new `## Regimes` section: spec-anchored = protocol and content schemas, decisions, requirements, journeys and the `spec.md` index, maintained and validated for the life of the product; spec-first = FEAT bodies and task tables, written to cut the work and frozen as history, with `status` from `in-progress` on and the task `State` derived by tooling, never edited by hand), `sdd-constitution` (an `AGENTS.md` line and a `spec.md` paragraph declare the regimes) and the `spec-index.md` and `spec-feature.md` templates (derived-status comments, no key added to the frontmatter). Why: assessment §4.6 and §6 E0, 128 `todo` task rows after about 35 merged PRs in stratics-docs and a PR template asking for a FEAT status edit that the contributing rules forbid; the taxonomy is Böckeler, "Understanding Spec-Driven-Development: Kiro, spec-kit, and Tessl" (martinfowler.com, 2025-10-15, opened 2026-10-06). Proof: `platforms/tools/check.sh`, `smoke.sh`, the unittests and `check_kit.py --links` pass; `sdd-process.md` 49 -> 55 lines (cap 60).
- `sdd-implement` §2 gates each task on its proof (`/goal <proof command> exits 0` set by the user in Claude Code, syntax checked at code.claude.com/docs/en/goal on 2026-10-06; the Proof section of the PR body re-run by the reviewer in Devin) and requires a screenshot or GIF for a visual change; `reviewer` and `validate-implementation` now always run `git worktree remove --force` plus `git worktree prune` after the clean checkout, even on failure. Why: assessment §5 verification row and §6 C3; stratics-docs DPRO-011 records 53 worktrees and 61 branches left behind after batch-20261004-141711. Proof: cleanup sequence run once (worktree count unchanged, see PR), the four kit gates pass.

### Removed
- `plugins/architect-sdd/skills/sdd-analyze/` and `plugins/architect-sdd/skills/sdd-audit/` (merged into `sdd-check`).

### Migration
- `/sdd-analyze` and `/sdd-audit` no longer exist as user-invoked names; run `/sdd-check FEAT-nnn validator=<output of check_spec.py 2>&1>` instead. Projects that mention the old names in `AGENTS.md`, FEAT `## Audit` comments or session notes should rename them at their next sync.

### Fixed
- `platforms/kits/INDEX.md`: the `docker/` row described a PostgreSQL+Redis compose; the compose ships PostgreSQL + Mailpit with an optional Valkey service commented out (Redis was replaced earlier). Found in the Stratics architect review of P2-01.

## [10.3.0] - 2026-10-06

### Added
- The journey layer: `journey.schema.json` (`platforms/ci/schemas/`), the `spec-journey.md` template and the `sdd-journey` skill. `docs/spec/journeys/J-NN.md` files hold one user-visible flow whose steps cite REQ ids, task rows and test paths; a rule a journey exercises is promoted to a REQ-F. Evidence: stratics-docs DPRO-013; seven journeys on main since 2026-10-05.
- `platforms/ci/validations/spec_trace.py`: journey↔REQ↔FEAT↔test traceability checker (`check`, `generate`, `impact`, `mark-done`, `status`), a generic copy of stratics-docs' `tools/spec-trace/spec_trace.py` — the spec directory is an argument, test paths root at the spec's own repository name, any sibling clone directory or a `--repo` extra, and journeys require `owner`. Self-test: `platforms/ci/validations/test_spec_trace.py`. Verified green on the real stratics-docs corpus: 7 journeys, 83 steps, 40 REQs.
- `platforms/ci/validations/pr_gates.py`, `platforms/kits/github/workflows/pr-contract.yml` and the `review-gates` skill (infra-github): the no-model PR gates as a reusable `workflow_call` check. A JSON config drives the Closes/proof-block/owned-areas/protected-paths/overlap/fragment/allowlist/CI gates — nothing project-specific is hardcoded; `proof-commands` is an output for the caller's `proof` job, which runs them with its own toolchain. Evidence: stratics-docs R-07 (`ops/review-loop/gates.py` + `reusable-pr-contract.yml`, merged as #342).
- `collab-two-humans` skill (core): the ten rules of the road for one backlog shared by two humans and their agents, as condition → action lines. Evidence: stratics-docs CONTRIBUTING.md §9 (R-10).
- `sdd-process.md` § "Variant: one issue per task with a review loop": per-task issues with `Complexity`, `model` and `Wave` fields and the same gates before review — a documented alternative to the per-FEAT card, not a new default. Evidence: stratics-docs `docs/spec/ARCHITECT.md` deltas 1–2.

### Changed
- `dev-java` template `project-agents-java-spring.md`: Java 25 / Spring Boot 4.x with explicit choice blocks — `Persistence: JdbcClient + Flyway (default) | JPA` and `Errors: project protocol catalog | RFC 7807`.
- `platforms/kits/github/workflows/ci-godot.yml`: reusable `workflow_call` workflow with `godot-version`/`test-runner` inputs — gdUnit4 by default, GUT optional, missing runner or zero suites fails; change-aware `changes` job and LFS cache.
- `platforms/kits/github/workflows/ci-java.yml`: reusable workflow with a `changes` job, required `NVD_API_KEY` secret, pinned `dependency-check-maven:13.0.0` and NVD cache saved even on failure.
- `platforms/kits/docker/compose.yml`: `postgres:18` (data dir under `/var/lib/postgresql`) and Mailpit; Redis replaced by a commented optional Valkey service.
- `postgresql` skill: `postgres-17.md` renamed to `postgres-18.md` with the PG 18 facts and data-dir change.
- Machine facts moved out of shared docs (`docs/maintenance.md`, `godot-4-versions.md`, `java-25-lts.md`) into git-ignored `docs/machine.local.md` — template at `docs/machine.local.md.example`; `.env` is now git-ignored.
- `sync-project.sh`: a project with `docs/spec/journeys/` now also receives `journey.schema.json` and `spec_trace.py` in its `.github/spec-lint/`; projects without journeys are unchanged.

## [10.2.0] - 2026-10-06

### Added
- `feature.schema.json` and the `spec-feature.md` template: optional `scope` field, a unique list drawn from `server`, `client` and `docs`, naming the repositories a FEAT touches. Evidence: all 52 Stratics FEATs carry `scope`, and stratics-docs' synced `.github/spec-lint/schemas/feature.schema.json` already accepts it, because it was synced from a kit checkout that had this change uncommitted (`git log -S'"scope"'` finds nothing on kit main). Syncing from kit main would reject every FEAT with "Additional properties are not allowed ('scope' was unexpected)".
- `sync-project.sh`: `--workflow <file>` names the project CI file that runs `check_spec.py` (default `spec-lint.yml` when install copies the kit workflow). Without the option, `--check` accepts any file under `.github/workflows/` containing `check_spec.py`, and install copies the kit workflow only when the project has none. Evidence: stratics-docs folded the validator into `docs-checks.yml`, so `--check` failed with "sync: spec-lint.yml missing" on a correctly synced project.

### Changed
- `check_spec.py`: FEAT `requirements:` and REQ `features:` must now agree. A link listed on one side only fails, in either direction. This replaces the one-way "REQ not listed in any FEAT" check, which the new rule covers. Evidence: on stratics-docs main `9c94767d7` (2026-10-05), FEAT-052 listed REQ-F-001 and REQ-F-003, but neither REQ listed FEAT-052, and the previous check passed (fixed in stratics-docs#280). Self-test: `platforms/ci/validations/test_check_spec.py`, run by the kit's CI. Migration: a project whose links disagree fails spec-lint after its next `sync-project.sh`; fix the side that is missing the link.
- `sdd-tasks`: a pre-cut checklist (§5) runs before issues are created. It checks test paths in `Files`, cross-feature fields against the owning contract, proofs that run unattended in CI or gates, and neighbour files a task needs. Evidence: in Stratics batch-20261004-141711, 7 of 16 issues had review findings caused by the spec:
  - a Files cell with no test path (stratics-server#14);
  - config or CI files outside the cell (stratics-docs#83, #84);
  - contract fields owned by another feature (#187, stratics-server#18, #196, #125);
  - a manual-only proof (Mailpit capture).

## [10.1.0] - 2026-10-04

### Changed
- `reviewer` / `validate-implementation`: review the pushed head on a clean checkout and re-run every proof command the author's report claims. A result not reproduced there is unverified, and one that fails there is a blocker. A proof that cannot fail (zero tests, zero schemas) is not proof. Evidence from the 2026-10-04 Stratics reviews:
  - stratics-server#13 reported `grep … exit=1`, but the fix was never committed and the grep matched 3 lines at the pushed head;
  - stratics-docs#136 claimed "manifest matches schema", but no step validated it;
  - stratics-docs#133's check was green only because `protocol/` had no schemas yet, and it crashed on the first real `$ref`.
- `github-cli`: after `gh pr create`, wait for the PR checks (`gh pr checks <n> --watch`) and report each check by name and conclusion, failures first. Local gates do not replace CI-only gates (dependency or secret scans), and a PR is not done while a check is red. Evidence: stratics-server#12 reported a green local `verify` while its CI `dependency-check` job was failing on two CVEs.

## [10.0.0] - 2026-10-03

### Changed
- **BREAKING — the single `ai-kit` plugin was split into twelve plugins.** `plugins/ai-kit/` is gone; content now lives in `plugins/core` (always-on rules, hook guard, session and kit-authoring skills), `plugins/dev-core` (code patterns), `plugins/dev-java`, `plugins/dev-godot`, `plugins/architect-core` (Clean Architecture, DDD, contracts), `plugins/architect-sdd` (SDD pipeline and `researcher`), `plugins/quality-core` (`reviewer`, skeptic, verdicts), `plugins/quality-security`, `plugins/infra-core`, `plugins/infra-persistence`, `plugins/infra-github`, plus the manifest-only `plugins/all` bundle that installs everything through dependency resolution.
- Satellites declare their parent through `requiredPlugins` (Devin) / `dependencies` (Claude): `dev-java`→`dev-core`→`core`. The root meta-plugin requires the `all` bundle, so `devin plugins install <repo>` restores the everything-installed behavior; every content plugin is listed as optional for minimal installs via `…#plugins/<name>`.
- The Claude marketplace gained a `renames` entry (`ai-kit`→`core`) and a `category` per plugin; legacy Devin installs should remove the old `ai-kit` plugin (`devin plugins remove ai-kit`) since its path no longer exists.
- Vendor skills moved to their owning plugins; `skills.lock` gained a `plugin` column and `vendor.sh` routes by it.
- `check_kit.py` was rewritten for the multi-plugin layout: it discovers plugins by manifest, validates the dependency graph (existence, no cycles, `agent:` reachability), enforces `core`-only `AGENTS.md`/`hooks` and the manifest-only `all`, and keeps the previous schema/parity/link/vendor gates.
- `doctor.sh`/`bootstrap.sh`/`refresh.sh`/`smoke.sh` iterate `plugins/*`: Claude rule symlinks are now `~/.claude/rules/<plugin>-<rule>.md`, Codex installs each marketplace entry, Claude installs the `all` bundle, and the shared `AGENTS.md` target is `plugins/core/AGENTS.md`.

### Migration
- Devin: `devin plugins remove ai-kit` then `devin plugins install ChristianPrzybulinski/agent-rules-kit` (full kit via `all`); satellites install individually via `…#plugins/<name>` and pull their dependency chain.
- Codex/Claude: marketplace re-add picks up the new catalog; Claude installs `all@ai-kit` (or any satellite — dependencies resolve), Codex installs entries individually. `doctor.sh` repairs AGENTS.md/rule/fallback symlinks.

## [9.0.0] - 2026-10-02

### Added
- Added Claude Code plugin and marketplace manifests, offline validation in CI, and zero-copy CLAUDE.md/rule symlinks.
- Added a shared local-Devin/Claude PreToolUse guard hook for destructive commands and `researcher`/`reviewer` custom subagent profiles.
- Five skills now run through a named or built-in subagent: SDD analyze/audit, implementation validation, vulnerability scanning and investigation.

### Changed
- User-only, subagent, agent-tool and path-rule metadata now carries and validates equivalent Devin, Codex and Claude Code keys.
- Java and Godot glob rules now load one standard skill, which points to Clean Code and testing guidance for Devin Cloud's one-active-skill limit.
- Doctor now merges the narrowed `read_config_from` policy while preserving other Devin configuration and manages Claude marketplace/plugin state.
- **BREAKING — plugin content moved to `plugins/ai-kit/`:** the repository root is now a content-free meta-plugin following Cognition's team-marketplace pattern and requires the real plugin through `git-subdir`. Devin's install source remains `ChristianPrzybulinski/agent-rules-kit`; the Codex marketplace resolves `./plugins/ai-kit`; doctor repoints `~/.codex/AGENTS.md` from either legacy target to `plugins/ai-kit/AGENTS.md`. The validator enforces the meta-plugin contract, plugin container and escape boundaries.

## [8.0.0] - 2026-10-01

### Changed
- Own skill frontmatter no longer carries the unused `version` key; `write` tool declarations use the supported `edit` capability.
- **BREAKING — 8.0.0 layout v6:** the repository root is now the Devin and Codex plugin. Always-on instructions, triggered rules, flat skills, references and templates are delivered directly from `main`; plugin manifest versions equal `VERSION`.
- Agent consumption is plugin-first. Devin Cloud fetches `main` per session, local Devin refreshes its plugin cache, and Codex uses its marketplace plugin with a temporary compatibility fallback.
- The `evidence` skill was merged into `skeptic`; knowledge notes moved under their owning skills as references.
- `AGENTS.md` 97 → 57 lines (9.7 KB → 4.4 KB): Craft, Tests, Git/docs and the Specialties table left for the skills that own them (`clean-code`, `clean-architecture`, `simplicity`, `ddd-and-patterns`, `testing`, `branching-and-versioning`, `update-docs`, `git-lfs`); Java/Godot routing moved to `rules/` globs. Every skill description ≤160 chars (total 6,803 of the 7,200 budget) with front-loaded triggers; ceremonies and side-effect skills are user-invoked only.

### Removed
- Removed the `agents/` level, prompts, separate knowledge tree, layout-state file, legacy install scripts and machine-managed Windsurf/Cursor/ChatGPT destinations.
- Removed the generated `devin-plugin` release branch and workflow; `main` is the release source.
- Removed the duplicate `grill-me` vendor skill; `grilling` remains.

### Added
- Added reference frontmatter schema, Codex user-only invocation policy files, allowed-tool validation, backtick-path validation and exact skill-index description checks.
- Added `rules/`, root Devin/Codex manifests, flat `skills/`, root `templates/`, and v6 schema/index/link validation.
- Added `bootstrap.sh`, `refresh.sh`, `doctor.sh`, `smoke.sh`, `vendor.sh`, and the six-hour launchd refresh agent.
- Added the 7,200-character skill-description budget and 40–160-character per-description gate for the Codex initial-list limit.
- Added the openai/codex#22078 fallback: doctor maintains Codex-only skill symlinks until the plugin exposes `ai-kit:*`, then removes them.

### Fixed
- Fixed lifecycle plugin detection under `pipefail`, added the required `codex plugin add ai-kit@ai-kit` installation step and prioritized the desktop app CLI wrappers.

## [7.3.0] - 2026-10-01

### Added
- `agents/skills/core/parallelize` — independent work leaves together: independent tool calls batched in one turn, long commands in the background while work continues, disjoint `[P]` tasks fanned out to subagents when the platform has them; names what must stay sequential (depends on a result, shares a file/index/port/DB, has an external side effect). New always-on line in `agents/AGENTS.md` (Work loop) and in `agents/prompts/chatgpt-full.md`.

### Changed
- `agents/AGENTS.md` 110 → 97 lines: sections whose detail a skill already carries in full (Session, Craft, Tests, Git/docs, Tokens) compressed to a summary line with a `Detail: skill …` pointer, after a line-by-line coverage check against `sessions`, `session-review`, `clean-code`, `clean-architecture`, `simplicity`, `ddd-and-patterns`, `testing`, `branching-and-versioning`, `update-docs`, `git-lfs`, `tokens`. Lines with no skill behind them (Truth, Skepticism, Security, Boundaries, Specialties, language, file size, ecosystem search, lint-config source) stay verbatim. "One PR, one concern" moved from Craft to the Session line. `agents/prompts/chatgpt-compact.md` unchanged (ChatGPT Custom Instructions have no tool calls to parallelize).

## [7.2.0] - 2026-10-01

### Added
- Devin plugin `ai-kit`: `platforms/install/devin-plugin.sh <out-dir>` builds `.devin-plugin/plugin.json` (version = `VERSION`), `AGENTS.md` (always-on rule, copy of `agents/AGENTS.md`) and the flattened `skills/<name>/`. `.github/workflows/devin-plugin.yml` publishes it to the generated `devin-plugin` branch on every push to `main`, so Devin sessions (cloud included) get the rules and skills without `bootstrap.sh`. Install from `https://github.com/ChristianPrzybulinski/agent-rules-kit` at ref `devin-plugin` (unpinned follows the branch; `devin plugins update ai-kit` re-fetches). `install-smoke.sh` now also builds the plugin and asserts `plugin.json`, `AGENTS.md` and the skill count.

## [7.1.2] - 2026-09-30

### Fixed
- `agents/prompts/chatgpt-full.md` said `Java 17+ (prefer 21 LTS)`; the kit standardizes on Java 25 LTS (`agents/knowledge/java/java-25-lts.md`, `platforms/kits/java-maven/`, `ci-java.yml`). Now `Java 25 LTS (fixed per project via toolchains.xml)`.

## [7.1.1] - 2026-09-30

### Added
- `platforms/tools/install-smoke.sh` — installs the kit twice into a throwaway `HOME` (idempotency), plants unmarked user skills, runs `all.sh --clean` and asserts they survive, every kit skill carries its marker and the always-on files match `agents/AGENTS.md`. Runs in `ci.yml`; it would have caught the `--clean` data loss fixed in 7.1.0.

## [7.1.0] - 2026-09-30

### Fixed
- `platforms/install/all.sh --clean` no longer deletes `~/.config/devin/skills` wholesale (user-owned skills were lost; `refresh.sh` runs `--clean` automatically on a `LAYOUT_VERSION` change). Legacy kit-named folders there are still removed by `install/devin.sh`.
- `check_spec.py` and `check_kit.py` now enforce `format: date` (`jsonschema.FormatChecker`): a `docs/spec/spec.md` left with the template placeholder `updated: "YYYY-MM-DD"` fails the lint instead of passing. Projects: rerun `platforms/tools/sync-project.sh <repo>` to pick up the new validator.
- Stale pre-v5 path in `agents/knowledge/postgresql/postgres-17.md` (`kits/docker/compose.yml` → `platforms/kits/docker/compose.yml`); `docs/maintenance.md` prerequisites (system Python has `pyyaml`/`jsonschema`, `check.sh` runs in full mode locally); Portuguese example file names in `agents/templates/spec-feature.md` and `docs/projects.md`; `platforms/kits/INDEX.md` no longer calls `ci-java`/`ci-godot` "reusable" (they trigger on push/PR, not `workflow_call`).

### Added
- `platforms/kits/github/dependabot.yml` — weekly GitHub Actions updates for projects (same as the kit's own).
- "Do not use for…" sentence in the 19 skill descriptions that lacked it — `check.sh` is now warning-free.
- Language rule (English artifacts, pt-BR conversation) in `agents/prompts/chatgpt-{full,compact}.md`, missing since v5.0.0.

### Changed
- Project workflow templates bumped to current majors: `actions/setup-java` v4→v6, `actions/cache` v4→v6, `actions/upload-artifact` v4→v7 (`ci-java.yml`, `ci-godot.yml`). The kit's own workflows were already current.

## [7.0.0] - 2026-09-30

### Changed
- **BREAKING (spec contract)**: spec `status` enum values are now English. Feature: `proposta`→`proposed`, `clarificada`→`clarified`, `planejada`→`planned`, `em-implementação`→`in-progress`, `validada`→`validated`, `entregue`→`delivered`, `cancelada`→`cancelled`. Decision: `proposta`→`proposed`, `aprovada`→`approved`, `rejeitada`→`rejected`, `substituída`→`superseded`. Debt: `aberta`→`open`, `paga`→`paid`, `aceita`→`accepted`.
- Updated everywhere the contract lives: `platforms/ci/schemas/{feature,decision,debt}.schema.json` (including the `substituída`→`superseded` conditional), `check_spec.py` STRUCT fallback, `agents/templates/spec-{feature,decision,debt,index}.md`, `platforms/kits/github/labels.json` (`status:*` labels), the `sdd-*` skills, `agents/skills/process/README.md` and `docs/projects.md`.
- Projects must rerun `platforms/tools/sync-project.sh` and migrate their `status:` values: `sed -i '' -e 's/^status: proposta$/status: proposed/' -e 's/^status: clarificada$/status: clarified/' -e 's/^status: planejada$/status: planned/' -e 's/^status: em-implementação$/status: in-progress/' -e 's/^status: validada$/status: validated/' -e 's/^status: entregue$/status: delivered/' -e 's/^status: cancelada$/status: cancelled/' -e 's/^status: aprovada$/status: approved/' -e 's/^status: rejeitada$/status: rejected/' -e 's/^status: substituída$/status: superseded/' -e 's/^status: aberta$/status: open/' -e 's/^status: paga$/status: paid/' -e 's/^status: aceita$/status: accepted/' docs/spec/**/*.md`

### Added
- README bootstrap note: `gh auth setup-git` so `refresh.sh`'s plain `git pull` reuses the `gh` credentials on a private repo (otherwise it warns and keeps the local state).

### Unchanged
- File names, IDs, frontmatter keys; `priority`/`severity`/`type` enums (already English).

## [6.0.1] - 2026-09-30

### Fixed
- `gitleaks` workflows: `pull-requests: read` permission added and PR comments disabled (`GITLEAKS_ENABLE_COMMENTS: "false"`) — the action lists PR commits on `pull_request` events (Dependabot PRs included) and failed with 403 "Resource not accessible by integration". Applied to the kit's own `.github/workflows/gitleaks.yml` and to the `platforms/kits/github` template.
- Vendor `VENDOR.md` stamps in English (`Do not edit — regenerate via platforms/install/third-party.sh.`); frontend-design license text corrected to `Apache-2.0 (LICENSE.txt in dir)`.

### Changed
- Actions bumped to the Node 24 runtime: `actions/checkout` v7, `actions/setup-python` v7, `gitleaks/gitleaks-action` v3 — supersedes Dependabot PRs #1–#3.

## [6.0.0] - 2026-09-30

### Changed
- **BREAKING**: `agents/rules/` removed — rules and skills were two artifacts with the same loading mechanism (`model_decision` ≡ `triggers: [model]`), duplicated in 5 pairs and invisible to Codex/Windsurf. Every rule is now a skill (normative content in `SKILL.md` or in the skill's `references/`). Mapping: merged into the sibling skill (`git/github-cli`, `java/java`, `godot/godot-2d`, `documentation/documentation`); moved as `references/` (`java/build-and-dependencies` → `java-standards`, `git/git-lfs-and-binaries` → `git-lfs`, `documentation/living-docs` → `update-docs`); converted 1:1 (`core/` = `evidence`, `sessions`, `tokens`; `development/` = `clean-code`, `simplicity`, `testing`, `twelve-factor`, `clean-architecture`, `ddd-and-patterns`; `tooling/branching-and-versioning`; `quality/secure-development`).
- Skills install into `~/.agents/skills/` (read natively by Devin, Cursor and Codex) and `~/.codeium/windsurf/skills/` — flattened by basename with the `.agent-rules-kit` marker; unmarked folders are never touched.
- `cursor.sh` removed: Cursor reads `~/.agents/skills` natively; `all.sh` removes the legacy `~/.cursor/rules/*.mdc` it used to generate.
- `LAYOUT_VERSION` 5: `refresh.sh` forces a full reinstall (`all.sh --clean`).

### Added
- `agents/skills/core/` type (`evidence`, `sessions`, `tokens`, `session-review`).
- Skill `session-review` (core): end-of-session summary and review of the session against the kit — at most one proposal (knowledge note, skill, `AGENTS.md` line, description fix or template), only with evidence from the session, asked before anything is written. `AGENTS.md` §Session gains the "End" bullet; the `skeptic` bullet under Skepticism gives way (already in the Specialties table).
- `platforms/install/skills.sh`: one installer for both skills destinations.
- `check_kit.py`: `core` skill type, `agents/rules/` now forbidden, `references/*.md` check (≤60 lines + linked from the SKILL.md).

### Removed
- `agents/rules/` (with its INDEX), `platforms/ci/schemas/rule.schema.json`, `agents/templates/kit-rule.md`, `platforms/install/cursor.sh`.
- Destinations `~/.devin/rules`, `~/.config/devin/skills` and `~/.codex/skills` (legacy cleanup on install).

### Fixed
- Stale skill names in the "Specialties" table of `AGENTS.md` (`core/*`, `java/*`, `godot/*`, `docs/*` prefixes dropped).

## [5.0.0] - 2026-09-30

Shipped with `LAYOUT_VERSION` 5 by mistake (no layout change in this version); harmless — 6.0.0 is the real layout 5.

### Changed
- **BREAKING (for readers)**: every artifact of the kit is now written in English — `AGENTS.md`, rules, knowledge, skills, templates, prompts, indexes, docs, scripts, schema descriptions and kits. The conversation with the user stays in pt-BR (rule unchanged).
- Classification tags renamed: `[FATO] [DECISÃO] [PROPOSTA] [HIPÓTESE] [BLOQUEIO]` → `[FACT] [DECISION] [PROPOSAL] [HYPOTHESIS] [BLOCKER]`. Deliberate-simplification marker: `// simplified: <ceiling>, <when to evolve>`.
- `check_kit.py`: language-dependent checks now expect English (`Load|Use` in rule descriptions, `Use`/`Do not use` in skill descriptions, `Must|Never|Always` normative warning in knowledge); output prefixes `FAIL:`/`WARN:`.
- `AGENTS.md` token cost (tiktoken): pt-BR 3023 (cl100k_base) / 2675 (o200k_base) → en 2442 / 2447 (−19% / −9%); 110 lines both.

### Unchanged (deliberate)
- Spec schema enum values (`proposta`, `aprovada`, `aberta`, …) and template frontmatter values: they are a contract with project specs; they move to English together with the project spec translation.
- File and folder names, skill names, frontmatter keys, IDs.

## [4.1.0] - 2026-09-30

### Added
- `platforms/tools/sync-project.sh`: copies `check_spec.py` + spec schemas + `spec-lint.yml` into the project's `.github/spec-lint/` (with `KIT_VERSION` and a generated README); `--check` detects divergence.
- Language rule: written artifacts in English; conversation with the user in pt-BR — in `AGENTS.md`, `clean-code.md` and `documentation.md`; short, purposeful names.

### Changed
- `platforms/kits/github/workflows/spec-lint.yml`: no kit checkout/token — runs the local copy in `.github/spec-lint/` (`CI=1` requires pyyaml/jsonschema in `check_spec.py`).
- `platforms/kits/sdd/init-spec.sh`: calls `sync-project.sh` — the project is born with spec CI.

### Removed
- Project dependency on the kit repo in spec CI (checkout + token removed). Reusable workflows between repos of the same product remain allowed.

## [4.0.1] - 2026-09-30

### Fixed
- `refresh.sh` and `bootstrap.sh` missing the executable bit after the `git mv`; `check_kit.py` now requires `+x` on every `platforms/**/*.sh`.
- `README.md`: bootstrap via `gh repo clone` (private repo; `curl raw` does not authenticate).

## [4.0.0] - 2026-09-30

### Changed
- **Layout v4**: `rules/`, `knowledge/`, `prompts/` → `agents/`; skills by type in `agents/skills/<type>/`; `processes/sdd/` → `agents/skills/process/`; flat templates in `agents/templates/` (`spec-*`, `doc-*`, `project-*`, `kit-*`); `schemas/`, `scripts/` → `platforms/ci/` and `platforms/tools/`/`platforms/install/`; `kits/` → `platforms/kits/`. Master index: `INDEX.md`.
- **BREAKING**: public paths changed — `scripts/check.sh` → `platforms/tools/check.sh`, `scripts/install/all.sh` → `platforms/install/all.sh`, `templates/docs/spec/*` → `agents/templates/spec-*`. Projects must update references (e.g.: `spec-lint.yml`).
- `check.sh` now delegates to `platforms/ci/validations/check_kit.py` (layout, frontmatters, indexes, links, lock, duplication); `--spec` remains in `check_spec.py`.
- `devin.sh`/`codex.sh` install skills from `agents/skills/`; `cursor.sh` ignores `INDEX.md`; `all.sh` writes `~/.config/agent-rules-kit/{VERSION,LAYOUT_VERSION}` and gains `--clean`.
- Releases are now automatic: tag `v*` → workflow validates `VERSION` and publishes a release with the changelog section.

### Added
- `VERSION`, `LAYOUT_VERSION`; root `INDEX.md` + INDEX/README in every folder.
- `platforms/tools/`: `bootstrap.sh` (1 command) and `refresh.sh [--quiet]` (pull + reinstall by version/layout).
- `.github/`: `ci`, `gitleaks`, `release` workflows; `dependabot.yml`; PR template; CODEOWNERS.
- `platforms/ci/schemas/`: `rule`, `knowledge`, `skill`, `skills-lock` (besides the 5 spec schemas).
- `agents/rules/core/sessions.md` (session hygiene) and `agents/templates/kit-*.md` (templates for the kit itself).
- `docs/`: `design.md` (principles), `projects.md` (what lives in the project), `maintenance.md` (versioning, vendor, CI).
- `knowledge.schema.json` frontmatter on the 9 `agents/knowledge/` notes.

## [3.2.0] - 2026-09-30

### Added
- Rule `rules/development/simplicity.md` (YAGNI ladder → already exists → stdlib → platform → minimum that works; deliberate simplification with a ceiling comment).
- Vendor of 5 third-party skills pinned by commit in `kits/third-party/skills.lock` + `scripts/install/third-party.sh` (sparse clone `--filter=blob:none`, copies the whole directory, `VENDOR.md`, `--check`): `grill-me`, `grilling` (mattpocock/skills, MIT); `skill-creator`, `frontend-design` (anthropics/skills, Apache-2.0); `find-skills` (vercel-labs/skills, MIT).
- `codex.sh` installs skills into `~/.codex/skills/<name>/` with an `.agent-rules-kit` marker (user content and `.system` preserved).
- Knowledge: `git/worktrees.md` (`git worktree`, when to use, pitfalls).

### Changed
- `AGENTS.md`: pragmatic Clean Architecture (port only at a real boundary), simplicity ladder in Craft, Tokens section split into two lenses (technical vs. text for people), new lines in Specialties (`/grill-me`, `skill-creator`, `find-skills`).
- `rules/development/testing.md`: YAGNI outside the domain — one executable check for non-trivial logic instead of a per-function suite.
- `rules/architecture/clean-architecture.md`: pragmatism — an internal service with one implementation is a concrete class.
- `rules/core/tokens.md`: rewritten for the two communication lenses.
- `processes/sdd/sdd-implement`: two-stage review.
- `processes/sdd/sdd-tasks`: smaller tasks.
- `templates/docs/review-checklist.md`: "when receiving review" section.
- `devin.sh` copies each skill's whole directory (was only `SKILL.md`); includes `skills/vendor/` in the flattening.
- `all.sh` runs `third-party.sh --check` before the other installers.

### Credits
- Ideas absorbed from JuliusBrussee/caveman, blader/humanizer, DietrichGebert/ponytail, obra/superpowers (all MIT) — not installed; the kit's policy is to absorb, not stack personas.

## [3.1.1] - 2026-09-30

### Fixed
- `scripts/check_spec.py`: `REQ-NF-nnn.md` files were not recognized by the ID prefix (regex `REQ-[FN]`); now `REQ-NF|REQ-F`.

## [3.1.0] - 2026-09-30

### Added
- Skills: `session-handoff`, `protocol-contract`, `investigate` (core), `characterization-tests` (java), `asset-import` (godot).
- Doc templates: `session-handoff`, `contract-message`, `recovery-report`, `bug-report`, `review-checklist`, `load-test` in `templates/docs/`.
- Knowledge: `godot/networking-transports.md` (client↔server transports in Godot 4 with a non-Godot server), `legacy/director-lingo-glossary.md` (Director/Lingo glossary for reading the legacy archive).
- FEAT schema: optional `milestone` and `evidence` fields.

### Changed
- `AGENTS.md`: new lines in the Specialties table for the 5 new skills.
- `templates/docs/spec/feature.md` updated alongside the schema.

## [3.0.0] - 2026-09-29

### Changed
- Structure reorganized by domain: `rules/<domain>/`, `skills/<domain>/<name>/`, `templates/{projects,docs}`, `prompts/`, `scripts/install/`. Skills renamed to unique names (`java-standards`, `godot-standards`, `update-docs`) because Devin installs skills into a flat folder.
- `AGENTS.md`: Tests and Git/docs/versioning sections; routing to rules/skills/process by context; security gates (0 critical/high CVEs, Argon2id, twelve-factor).
- Installers rewritten (`devin.sh`, `cursor.sh`, `windsurf.sh`, `codex.sh`, `all.sh`); `check.sh` validates rules/skills/processes, sizes, schemas and, with `--spec`, a project's `docs/spec`.

### Added
- Rules: `testing` (100% line/branch + PITest ≥80% in the domain; happy+sad integration), `twelve-factor`, `secure-development`, `ddd-and-patterns` (when-yes/when-no catalog), `branching-and-versioning` (trunk-based, expiring feature flags, SemVer, `protocol_version`), `git-lfs-and-binaries`, `java/build-and-dependencies` (Maven required, fixed LTS), `living-docs`.
- Skills: `validate-implementation`, `vuln-scan`, `git-lfs`, `postgresql`, `redis`, `docker`, `dbeaver`, `krita`.
- `sdd` process (Spec-Driven Development) adapted from github/spec-kit: `sdd-constitution`, `sdd-specify`, `sdd-clarify`, `sdd-analyze`, `sdd-audit`, `sdd-plan`, `sdd-tasks`, `sdd-implement`, `sdd-to-card` (GitHub Issues + Projects). Prefixes `FEAT/REQ-F/REQ-NF/DEC/DEBT`, per-feature status, `[FATO]/[DECISÃO]/[PROPOSTA]/[HIPÓTESE]/[BLOQUEIO]` classification.
- Spec templates (`spec`, `feature`, `requirement-functional`, `requirement-non-functional`, `decision`, `debt`) and the corresponding JSON Schemas.
- Kits: `github` (ci-java, ci-godot, spec-lint, gitleaks workflows; PR template; labels), `java-maven` (pom-parent with gates), `docker` (Postgres 17.11 + Redis 7.4), `git-lfs`, `godot`, `sdd/init-spec.sh`.
- `knowledge/` with dated factual notes (Java 25 LTS, Godot 4.7, Postgres 17, Redis 7 and license, Compose v5, LFS quotas).
- Installation for Codex CLI (`~/.codex/AGENTS.md`).

### Fixed
- GitHub LFS quota corrected to 10 GiB (Free/Pro), per current docs.

### Removed
- `scripts/install.sh` and `scripts/to-mdc.sh` (replaced by `scripts/install/*`); installation into `~/.claude/CLAUDE.md`.

## [2.0.0] - 2026-09-29

### Changed
- `AGENTS.md` rewritten in the condition→action model, ordered by half-life, with Truth, Skepticism (>98%), Loop, Craft, Boundaries (Always/Ask/Never) sections and a skill routing table.
- Rules `00-core`, `10-clean-code`, `20-clean-architecture`, `70-token-efficiency` move from `always_on` to `model_decision` — the summary lives in `AGENTS.md`; detail loads on demand (fewer tokens per session).
- `PROMPT.md` restructured as a full system prompt.
- README rewritten with evidence-based design principles and script-based installation.

### Added
- `skeptic` skill: adversarial verification (against → for → verdict with confidence).
- `templates/java-spring/AGENTS.md` and `templates/godot-2d/AGENTS.md` with stack, commands, condition→action patterns and boundaries.
- `PROMPT-compact.md` (≤1,500 chars) for ChatGPT Custom Instructions.
- `scripts/install.sh` (installs and validates) and `scripts/to-mdc.sh` (generates `.cursor/rules/*.mdc`).
- Installation for Cursor (`~/.cursor/rules`) and, optionally (`--claude`), Claude Code (`~/.claude/CLAUDE.md`).

### Removed
- Installation into `~/.devin/global_rules.md` (duplicated `~/.config/devin/AGENTS.md` in the context).

## [1.0.0] - 2026-09-29

### Added
- Initial structure: `AGENTS.md`, rules by domain, `java`, `godot-2d`, `github-cli`, `docs` skills, `PROMPT.md`.
