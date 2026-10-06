# Changelog

Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/). Versioning: [SemVer](https://semver.org/).

## [Unreleased]

### Added
- `docs/plans/2026-10-kit-assessment/`: assessment of v10.1.0 against current Anthropic, Cognition and market guidance for the Stratics Godot 2D client + Java server, plus 34 self-contained execution prompts in three phases (freeze layout and fix contradictions; distribute by repository commit and consolidate skills; Godot online 2D references, Devin environment, process-loop plugin, evals and KPIs). Evidence: review-loop first-pass rejection rate 20 of 33 PRs (stratics-docs DPRO-011); 24 of 25 destructive commands pass the hook guard; stale kit paths cited in stratics-docs; FEAT task tables with 128 `todo` rows after ~35 merged PRs.
- `sync-project.sh --check` now scans the project's `*.md` for obsolete kit paths (layouts 1.x to 9.x: `agents/skills/`, `agents/rules/`, `agents/knowledge/`, `rules/godot/`, `rules/java/`, `rules/git/`, `kits/java-maven/`, `kits/github/`, `platforms/install/`, `knowledge/`, `processes/sdd/`, `plugins/ai-kit/`) and fails listing each `file:line`; a historical citation opts out with `<!-- kit-path-ok -->`, and `legacy/`, `docs/sessions/` and `.claude/` are skipped (vendored copies under `.claude/` are verified by their own manifest). Why: consumer specs cite kit paths and every past layout change silently invalidated them (assessment §6 A3) — stratics-docs cited `agents/skills/process/README.md` (`AGENTS.md:20`), `kits/java-maven/pom-parent.xml` and `rules/java/build-and-dependencies.md` (DTEC-001), `rules/godot/godot-2d.md` (DTEC-002), `knowledge/redis/` (DTEC-003), `rules/git/branching-and-versioning.md` (DPRO-001) and `rules/git/git-lfs-and-binaries.md` (DPRO-006); none exist (`ls agents rules knowledge kits processes platforms/install plugins/ai-kit` at the kit root: all absent). Proof: `platforms/ci/validations/test_sync_project.py` exercises the scan on a throwaway repo in 5 unittest cases discovered by the kit's CI.

### Changed
- The 10.x layout is declared frozen until at least 2027-01-01: new "Layout stability" principle in `docs/design.md`; `docs/maintenance.md` now classifies content changes (MINOR adds a rule, skill, reference, template, validator gate or document; PATCH corrects one without changing routing); the PR template replaces the dead `LAYOUT_VERSION` checkbox with a no-layout-change check. `docs/projects.md` no longer cites `platforms/install/` (removed in 8.0, `## [8.0.0]` `### Removed`) or describes a separate "knowledge" tree (folded into references in 8.0): content reaches the agent through the plugin marketplaces or `bootstrap.sh`. Why: layout changes in 4.0, 6.0, 8.0, 9.0 and 10.0 each forced `bootstrap`/`doctor` re-runs and invalidated consumer citations, so paths are now a contract (assessment §4.1, §6 A3). Proof: `grep -n 'platforms/install\|knowledge' docs/projects.md` prints nothing and `grep -c 'LAYOUT_VERSION' .github/PULL_REQUEST_TEMPLATE.md` prints 0.
- `godot-standards` section 3, the `project-agents-godot-2d.md` template and `editor_settings_hints.md` no longer prescribe `_physics_process` + `move_and_slide()`; the movement model is declared per project in `AGENTS.md` (option A physics bodies, option B grid/tile-step with a server-authoritative position, prediction of at most one step and tween/lerp presentation in `_process`), never mixed in one entity (assessment §4.4, §6 D1; stratics-docs DGME-002; stratics-client `AGENTS.md:41`). Proof: `grep -rn 'Move a body' plugins/` prints nothing, `SKILL.md` shows 2 `Option A`/`Option B` lines, and `wc -l` of `SKILL.md` is 51 (limit 80).
- `plugins/core/AGENTS.md` section Skepticism rewritten as verifiable rules (an unsourced claim is tagged `[HYPOTHESIS]`; unblocked ambiguity -> decide and state the assumption in one line; a real blocker -> one question with 2-4 options and a recommendation), the numeric 98% confidence threshold removed from the global rules and from the `skeptic` policy and description, and the duplicate ambiguity lines in Work loop and Communication folded into Skepticism. Evidence: `AGENTS.md:15` ("Confidence < 98% -> do not proceed") contradicted `AGENTS.md:29` ("Ambiguous but unblocked -> decide, state the assumption, proceed"), so the agent picked one at random (assessment §4.4, item B1). Proof: `grep -n '98' plugins/core/AGENTS.md plugins/quality-core/skills/skeptic/SKILL.md plugins/quality-core/INDEX.md` prints nothing, `grep -c 'Ambigu' plugins/core/AGENTS.md` prints 1 and the file stays at 57 lines (limit 60).
- Godot boot proof in `godot-standards` §5, `reviewer` step 3, `validate-implementation` §3, the `project-agents-godot-2d.md` template and `ci-godot.yml` is now `godot --headless --path . --import` followed by `! godot --headless --path . --quit 2>&1 | grep -Eq 'SCRIPT ERROR|Parser Error'` (in CI the `--quit` line tees `boot.log` and the grep is the step's last line), because `--quit` exits 0 after a script error and skips the import scan (assessment §4.4, §6 D3; stratics-docs ARCHITECT.md delta 6, 2026-10-05; stratics-docs#84). Proof: `grep -rn -- '--headless --quit' plugins platforms` prints nothing, every remaining `--headless --path . --quit` is the grep form or the `tee boot.log` line, and the broken-case run is in the PR body.

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
