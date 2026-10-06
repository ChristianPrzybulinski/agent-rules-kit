# Assessment of agent-rules-kit v10.1.0 for Stratics development (2D game)

Date: 2026-10-06. Subject: `ChristianPrzybulinski/agent-rules-kit` on `main` (`ddd3ad2`, v10.1.0) and its real use in the `stratics-docs`, `stratics-client`, `stratics-server` repositories. Comparison with the current guidance from Anthropic (Claude Code 2.1.x, Agent Skills), Cognition (Devin, Devin Desktop/Windsurf) and the market (AGENTS.md, Cursor, Copilot, Codex, Spec Kit, Humanlayer, Thoughtworks, Godot ecosystem).

## 0. Executive summary

**Verdict.** The kit is above the market average in engineering (lean always-on context, skills in the open standard, mechanical validation, verification in a clean checkout, vendor lock) and below it in what weighs most on Stratics velocity: stability, portability and content specific to an online 2D game. The bottleneck measured by the project itself is not code standards: 61% of the review loop PRs were rejected on the first pass and most findings come from spec gaps and task cutting. The kit still describes a process (branch per FEAT, manual status, GUT, physics for movement) that the project has already abandoned, and each agent session receives part of that contradictory advice.

**The ten points that matter most.**

1. **Churn**: 10 MAJOR versions between 2026-09-29 and 2026-10-04; the repos cite kit paths that no longer exist. Freeze the layout and add a path gate (§4.1, A3).
2. **Portability**: the kit arrives through symlinks in `~/.claude`, `~/.codex` and user plugins; cloud sessions, GitHub Action and collaborators without `bootstrap.sh` run with no rules at all. Distribute by commit in the repository (`CLAUDE.md`→`@AGENTS.md`, `.claude/settings.json` with `enabledPlugins` per repo, versioned `.claude/rules/`, `.claude/skills/`) (§4.2, A1).
3. **Guard hook**: 24 of 25 destructive commands tested in the assessment session (2026-10-06) went through (`rm -r -f`, `git push +main`, `git restore .`, `docker compose down -v`, `flyway:clean`...). Cover what the skills promise, or use the official `security-guidance` plugin with project patterns (§4.3, C1).
4. **Contradictions that cost rounds**: `move_and_slide` vs tile-based movement (DGME-002), GUT vs gdUnit4, `--quit` with exit 0 after `SCRIPT ERROR`, coverage/mutation not applicable to GDScript, "98% confidence" vs "decide and proceed". Fix all of them in the first week (§4.4, B1, D1–D3).
5. **Generic Godot**: nothing in the kit about authoritative server, prediction/reconciliation, envelope codec, tests without `SceneTree`, generated files (`.uid`, `*.import`), 3.x→4.x syntax pitfalls. The best content is stuck in the client's `AGENTS.md`. Promote it to the kit as `godot-standards` references (§4.5, N1).
6. **SDD with ten steps and a status nobody can update**: 128 `todo` tasks with ~35 merged PRs; `spec.md` says "development not started". Derive status from GitHub, absorb the 8 deltas from `ARCHITECT.md`, create the prototype lane for game "feel", merge `analyze`+`audit` (§4.6, E1–E4).
7. **43 skills, 31 model-invocable, five overlapping** on "good code"; `frontend-design`, `find-skills`, `krita`, `dbeaver` do not help Stratics. Consolidate to ~30 and move the extras to an optional plugin (§4.7, F1–F3).
8. **What speeds up the project is outside the kit**: `loop.py` (1,343 lines), orchestrator and child prompts, verdict schema, proof allowlist, cutting checklist. Turn it into a `process-loop` plugin (§4.8, N4).
9. **Devin with no environment, playbook or fallback**: the kit's premise about Knowledge is correct (the official page declares it deprecated, migrating to skills in plugins), but the kit does not ship `environment.yaml`, a snapshot, Playbooks for the loop children, and it depends on the plugin as the only delivery path on Devin Cloud, where the plugin's subagents and hooks do not load and only one skill is active at a time (§5, N3).
10. **No measurement**: no skill evals and no process KPI. Use `claude plugin eval` on the 8 critical skills and extract from `ledger.csv` the first-round approval rate, rounds per PR and spec findings, batch by batch (§4.9, N5).

**What to keep as is**: the 58-line `AGENTS.md` and its test "stays only if no skill enforces it"; schemas and `check_kit.py`; `reviewer`/`validate-implementation` re-running proofs on the pushed head; `parallelize` (one writer, many readers); the vendor lock; the `[FACT]/[HYPOTHESIS]/[BLOCKER]` classes; the habit of changing the kit only with session evidence.

> Execution prompts for every item of §6–§8 live in [`prompts/`](prompts/README.md).

## Contents

- §0 Executive summary
- §1 What was assessed and how
- §2 Context: the game and the state of the project
- §3 What is right
- §4 What is wrong or fragile (4.1 churn · 4.2 portability · 4.3 hook · 4.4 contradictions · 4.5 generic Godot content · 4.6 SDD · 4.7 skills · 4.8 orchestration outside the kit · 4.9 measurement · 4.10 smaller items)
- §5 What Anthropic, Cognition and the market prescribe, and where the kit stands (5.1 market)
- §6 What to change (A distribution · B always-on · C hooks · D Godot · E SDD · F skills · G Java)
- §7 What to add (N1–N7)
- §8 Prioritized plan
- §9 Sources, evidence and limits

## 1. What was assessed and how

**Object.** `agent-rules-kit` v10.1.0 (branch `main`, commit `ddd3ad2`): 12 plugins, 43 skills, 3 glob-scoped rules, 18 templates, 14 references, 1 hook, 2 subagent profiles, validators (`check_kit.py`, `check_spec.py`), lifecycle scripts (`bootstrap.sh`, `doctor.sh`, `refresh.sh`, `sync-project.sh`, `vendor.sh`, `smoke.sh`) and the platform kits (`platforms/kits/*`).

**Real consumption.** The three Stratics repositories (`stratics-docs`, `stratics-client`, `stratics-server`) were read to see how the kit is used day to day: global installation in `~/.ai-kit`, per-repository `AGENTS.md` as a "delta" over the kit, generated copy of the spec validator in `stratics-docs/.github/spec-lint/`, and the project's operational mesh (DPRO-011 review loop, `ARCHITECT.md`, `CONTRIBUTING.md`, orchestrator prompts).

**Tests executed in the assessment session (2026-10-06).**

| Check | Result |
|---|---|
| `check_kit.py` with `CI=1` | OK (12 plugins, 43 skills, 3 rules, 18 templates, 17 indexes, 44 links) |
| `claude plugin validate` on `core`, `dev-godot`, `architect-sdd` and on the root marketplace | passed (Claude Code 2.1.290) |
| Skill description budget | 6,803 of 7,200 characters (94.5% used) |
| `plugins/core/AGENTS.md` | 58 lines, 4,335 characters, ~1.2k tokens |
| `PreToolUse` hook with 25 destructive commands outside the case table | 24 of 25 passed without being blocked (details in §4.3) |

**External sources.** Anthropic documentation and blog (Claude Code, Agent Skills, context engineering, harnesses), Cognition (Devin docs, the "Don't Build Multi-Agents" blog post and the 2026 follow-up, Devin Review, Knowledge, Playbooks, plugins), and the market (AGENTS.md/Agentic AI Foundation, Cursor, Copilot, Codex, Humanlayer, Spec Kit/Kiro/OpenSpec, Thoughtworks, Godot and Spring practices). The sources are in §9.

## 2. Context: the game and the state of the project

Stratics is a 2D pixel-art remake of a legacy MMORPG (Director/Lingo + OpenSMUS): grid-based open world, tile-based movement, turn-based tactical battles, multiplayer with an authoritative server. Godot 4.7.2 client (typed GDScript, Mobile renderer, gdUnit4), Java 25 + Spring Boot 4.1 + PostgreSQL 18 server (JdbcClient, Flyway, Testcontainers, ArchUnit), versioned JSON contract over WebSocket in `stratics-docs/protocol/`.

State as of 2026-10-05 (one week of work):

| Area | Size |
|---|---|
| Spec (`docs/spec`) | ~9.5k lines, 52 FEATs, 34 REQs, 43 approved decisions, 4 journeys |
| Client | ~690 lines of game GDScript, 46 gdUnit4 tests, no world/movement/battle yet |
| Server | ~2.5k new lines (hexagonal), 140 new tests, 12.7k lines of legacy in quarantine |
| Review loop | 33 PRs reviewed; 20 (61%) rejected on the first pass; 7 of 16 issues in one batch with defects caused by the spec itself |

This picture defines the assessment criterion: **the bottleneck today is not code standards, it is the quality of task cutting and verification**. The kit must be judged by how much it reduces review rounds and increases the rate of PRs approved on the first pass.

## 3. What is right

The points below coincide with what Anthropic, Cognition and the market recommend today. They are worth keeping and, in some cases, promoting.

1. **Lean always-on context.** Global `AGENTS.md` with 58 lines (~1.2k tokens), glob-scoped rules instead of `model_decision`, and the test "the line only stays if no skill can enforce the behavior" are exactly the "progressive disclosure" discipline that Anthropic prescribes for `CLAUDE.md` and Cognition for `global_rules.md` (6,000-character limit in Windsurf/Devin Desktop). The kit went from 110 to 58 lines across three versions, with token measurement in the CHANGELOG. This is rare and correct.
2. **Skills in the open Agent Skills standard.** `SKILL.md` with `name`/`description`, short body (≤80 lines), `references/` for dated facts with `sources`, and descriptions in the format "does X. Use when Y. Do not use for Z (skill W)". It is the format that Claude Code, Codex and Devin read natively; the 7,200-character budget for Codex's initial list is a real constraint and the kit treats it as a CI gate.
3. **Verification as a first-class concern.** `reviewer` and `validate-implementation` require re-running the proofs in a clean checkout of the submitted head, treat the "author's report" as a claim and reject proofs that cannot fail (zero tests). This is the right answer to the "verification gap" that Anthropic (harness for long-running agents) and Cognition (2025 performance report: "a recording does not prove correctness") point out. The evidence in CHANGELOG 10.1.0 (PRs #13, #136, #133) shows that the rule was born from real failures.
4. **One writer, many readers.** `parallelize` says to parallelize reads and serialize writes that share a file, index, port or database; `researcher` is read-only with `omitClaudeMd`. It is literally the model that Cognition defends in "Don't Build Multi-Agents" (2025) and refines in "Multi-Agents: What's Actually Working" (2026-04): single-threaded writes, extra agents contribute intelligence, not actions.
5. **Task cutting with executable proof.** `sdd-tasks` (5–30 min, ≤5 files, one proof per task, pre-cut checklist) and the `Files` field closed by a gate match Cognition's guidance for "junior-level, isolated, verifiable" tasks and what the project itself measured (the same three gaps caused 6 rounds).
6. **Hook tested in CI.** `hook_guard_cases.json` with blocked and allowed cases executed by the validator is best practice: hooks without tests break silently. The problem is coverage (§4.3), not the mechanics.
7. **Vendoring with a lock.** `skills.lock` with SHA, license and verification date, generated `VENDOR.md` and `vendor.sh --check` is the correct way to bring in third-party skills without losing traceability.
8. **Mechanical validation of everything.** JSON schemas for skill, rule, agent, reference and spec frontmatter; parity of the three manifests; dependency graph without cycles; verified links; shellcheck; bootstrap smoke test in an isolated HOME. Very few kits on the market have this.
9. **Claim classes (`[FACT]`, `[HYPOTHESIS]`, `[BLOCKER]`...)** and the rule "code read in this session is the only truth" reduce API/version hallucination, the number one LLM failure mode in GDScript (3.x syntax, invented APIs).
10. **Learning that closes the loop.** The latest versions (10.0→10.1→Unreleased) were born from evidence of real PRs cited in the CHANGELOG. This habit is what Cognition calls "Session Insights → Knowledge" and what Anthropic recommends for evolving `CLAUDE.md`: change only with session evidence.

## 4. What is wrong or fragile

Ordered by impact on speed and accuracy.

### 4.1 Kit instability: 10 MAJOR versions in 6 days

`CHANGELOG.md` records v1.0.0 on 2026-09-29 and v10.1.0 on 2026-10-04, with layout changes in 4.0, 6.0, 8.0, 9.0 and 10.0. The consumer repositories did not keep up:

- `stratics-docs/AGENTS.md:20` points to `agents/skills/process/README.md` (v4–v7 layout; today it is `plugins/architect-sdd/skills/sdd-constitution/references/sdd-process.md`).
- `DTEC-002:50` cites `rules/godot/godot-2d.md` and `DTEC-001:19,43` cites `kits/java-maven/pom-parent.xml`; neither exists anymore.
- The kit's own `docs/projects.md` mentions `platforms/install/` and `knowledge/`, folders removed in 8.0.

Each layout change forces re-running `bootstrap`/`doctor` on every machine and invalidates citations in the specs. The market (Anthropic, Cognition, AGENTS.md) converges on **stable, native formats** (`CLAUDE.md`/`AGENTS.md`, `.claude/rules`, `SKILL.md`), precisely so as not to depend on installation scripts. Recommendation: freeze the layout (declare 10.x stable for at least one quarter), treat paths as a contract and add to `check_kit.py` a gate that searches the consumer repos (via `sync-project.sh --check`) for references to nonexistent paths.

### 4.2 Portability: the kit does not exist outside the owner's machine

The kit is delivered through symlinks in `~/.claude/CLAUDE.md`, `~/.claude/rules/`, `~/.codex/AGENTS.md` and plugins installed at the user level. Observed consequences:

- None of the three repositories has `CLAUDE.md`, `.claude/settings.json` with `enabledPlugins`, or `.mcp.json`; only `AGENTS.md`. A Claude Code session on the web (like this one), a GitHub Actions runner, a Devin Cloud without the plugin installed in the org, or a human collaborator without `bootstrap.sh` run **with no global rule, skill or hook at all**. The project's `CONTRIBUTING.md` acknowledges this by requiring manual installation.
- `docs/maintenance.md`, `godot-4-versions.md` and `java-25-lts.md` carry "this machine" facts (Godot 4.7.2 installed, JDK 25 in `/opt/homebrew`, Claude Code 2.1.287). A shared kit with facts from one machine is an anti-pattern: for any other environment, it is false information stamped `[FACT]`.
- `stratics-docs/ARCHITECT.md`, `ops/review-loop/config.json`, `.devin/config.json` and the prompts have absolute paths `/Users/christian/...`.

The dominant practice in 2026 is "the repository carries what the agent needs": `AGENTS.md` + `CLAUDE.md` (or `@AGENTS.md`), `.claude/rules/*.md` with `paths:`, `.claude/skills/` (read by Claude Code **and** Devin), `.claude/settings.json` with `enabledPlugins` and `extraKnownMarketplaces`, hooks in `settings.json`. The kit remains the source, but distribution must be **by commit in the consumer repository** (via an extended `sync-project.sh`), not by symlink on the machine.

### 4.3 The guard hook promises more than it delivers

The `PreToolUse` blocks `rm -rf`, `git push --force`, `git reset --hard`, `git clean -f` and `DROP/TRUNCATE` via SQL CLI. Test run in the assessment session (2026-10-06) with 25 additional destructive commands:

| Passed without being blocked | Comment |
|---|---|
| `rm -r -f build`, `rm --recursive --force build`, `find . -delete` | trivial variants of `rm -rf` |
| `git push origin +main`, `git push origin :feature`, `git branch -D main` | force-push via refspec and branch deletion |
| `git checkout -- .`, `git restore .`, `git stash drop`, `git stash clear` | loss of uncommitted work |
| `docker compose down -v`, `docker system prune -af` | the `docker` skill says "ask first" for `down -v`; the hook does not enforce it |
| `./mvnw flyway:clean`, `psql -f drop_all.sql` | schema destruction |
| `git filter-repo --force`, `git lfs migrate import --everything` | history rewrite; the `git-lfs` skill says "ask before execution" |
| `gh repo delete x`, `terraform destroy`, `chmod -R 777 /`, `curl x \| sh` | external effect / security |

Only `rm -rf ~` was blocked. In addition, the emitted JSON (`decision: block`) is marked as deprecated for `PreToolUse` in the current documentation; the block only happens because the script also exits with code 2. The kit calls the hook a "guard, not guardrail", but the skills and the `AGENTS.md` ("Ask first: force-push; delete files you did not create") give the impression of coverage. Either the hook covers what the skills promise, or the promise is removed from the skills. As Anthropic recommends, what needs to be deterministic goes into a hook; the rest stays as instruction, without pretending to be a gate.

### 4.4 Internal contradictions that cost rounds

- **Movement.** `godot-standards` and the `project-agents-godot-2d.md` template mandate `_physics_process` + `move_and_slide()`; the project decided on tile-based movement without physics (DGME-002) and the client's `AGENTS.md` says "`move_and_slide`/`CharacterBody2D` is **not** the movement model". The glob-scoped rule loads `godot-standards` on every `.gd`, injecting the wrong advice on every edit.
- **Tests.** The kit and `ci-godot.yml` assume GUT; the project uses gdUnit4 (DTEC-010). The kit's CI template silently skips the tests if `addons/gut` does not exist ("skipping tests") and comes out green: exactly the "gate that cannot fail" that the same kit's `reviewer` forbids.
- **Godot exit code.** `godot-standards` and `validate-implementation` use `godot --headless --quit` as proof; the project discovered that the exit code is 0 even with `SCRIPT ERROR` (ARCHITECT.md delta 6) and started doing `grep -q 'SCRIPT ERROR'`. The kit has not yet absorbed this.
- **Coverage.** `testing` requires 100% line/branch + mutation ≥80% in the domain. This exists for Java (JaCoCo/PIT), not for GDScript (no mature mutation testing). For the client the rule is inapplicable and the agent either ignores it or makes something up.
- **Confidence.** `AGENTS.md` § Skepticism: "Confidence < 98% → do not proceed". § Work loop: "Ambiguous but unblocked → decide, state the assumption, proceed". The two rules collide; in practice the agent picks one at random. Anthropic's current guidance for autonomous agents is the second one.
- **Outdated Java template.** `project-agents-java-spring.md` says "Java [21], Spring Boot [3.x]", JPA and RFC 7807; the project uses Java 25, Boot 4.1, JdbcClient without JPA and its own error catalog. The kit's `pom-parent.xml` pins Boot 3.5.16, a line that left OSS support on 2026-06-30 (DTEC-009 asks to update the kit).
- **Decisions.** The project templates point to `docs/adr/` and `docs/design.md`; the same kit's SDD pipeline uses `docs/spec/decisions/`.

### 4.5 The Godot content is too generic for a 2D MMORPG

`dev-godot` has 3 skills: `godot-standards` (47 lines of generic best practices), `asset-import` and `krita` (art workflows, user-only). For the game being built, exactly the topics where LLMs err the most are missing:

- **non-authoritative** client: one-tile prediction + reconciliation, `move_rejected`, `BattleEvents` queue, no game rules on the client (today this exists only in the client's `AGENTS.md`, not in the kit);
- **determinism and testability** of scene-less logic: pure state in `RefCounted`, clock/RNG injection, gdUnit4 tests without `SceneTree`, `--ignoreHeadlessMode`;
- **network contract** in GDScript: JSON envelope codec, `protocol_version`, reconnection, `WebSocketPeer` heartbeat;
- **scenes and generated files**: `.uid`, `*.import`, `.translation` go into the task's `Files`; conflicts in `.tscn`; what never to edit by hand;
- **performance budget**: frame target, node limit per scene, pooling, generated `TileMapLayer`;
- **UI/i18n**: `TranslationServer`, pt-BR string table, themes;
- **model failure modes**: Godot 3 syntax (`onready var`, `export`, `yield`, `instance()`), nonexistent APIs, `get_node` in `_process`, `await` without a signal.

The client's `AGENTS.md` already encodes several of these rules, but they stay locked in the project; the kit should absorb them as `references/` of `godot-standards` (or as a `dev-godot-netplay` plugin), parameterized by the project's movement model.

### 4.6 The SDD has ten steps and none of them closes the loop with the code

- The spec has ~9.5k lines for ~3k lines of new code. `spec.md:13` still says "No development has started" and `:62` "in-progress FEAT: none" with ~35 implementation PRs merged.
- Task tables: 128 `todo` rows, 3 `done`; FEAT-009 T2/T3 are `todo` with the PRs merged.
- The PR templates ask for "FEAT status updated", but `CONTRIBUTING.md` forbids editing `docs/spec/**` and the Devin children can only touch the `Files` cell. Nobody can update the status; the rule exists to be violated.
- `sdd-implement` expects a `feature/FEAT-nnn` branch, squash per FEAT, status `in-progress → validated → delivered`; the project works with **one issue per task**, in worktrees, with one PR per task and merge by the loop. The kit describes a flow the project does not use; `ARCHITECT.md` carries 8 "deltas" to correct this.

Thoughtworks (Böckeler, 2025–26) and the market critique of Spec Kit/Kiro point to the same risk: ceremony that is neither read nor updated becomes "spec theater". The direction is to **derive status from GitHub** (merged PR → `done`, FEAT with all tasks `done` → `delivered`) with `spec_trace.py`/`project-sync`, and remove the manual status; and to incorporate the ARCHITECT.md deltas into `sdd-tasks`/`sdd-to-card` instead of keeping them outside the kit.

### 4.7 Too many model-invocable, overlapping skills

31 of the 43 skills can be loaded by the model from the description. Five of them (`clean-code`, `simplicity`, `testing`, `clean-architecture`, `ddd-and-patterns`) cover the same "write good code" territory and `godot-standards`/`java-standards` reference them in a chain. The kit itself records that Devin Cloud has a "limit of one active skill", and Anthropic warns that too many descriptions degrade selection. Likely result: the right skill does not load, or three load with redundant advice.

In addition:
- `find-skills` (vendor) has a 303-character description (above the 160 limit of the kit's own schema; the validator exempts vendors) and instructs installing third-party skills by popularity, a prompt injection vector that contradicts the kit's security posture;
- `frontend-design` is for the web; game UI in Godot does not benefit;
- `krita` and `dbeaver` describe GUI use by humans; they cost description budget with no gain for the agent;
- `tokens` defines "ultra" compression levels that conflict with "governed documents never compressed" and with the required pt-BR communication.

### 4.8 The orchestration that delivers speed lives outside the kit

What actually speeds up the project today is DPRO-011: `loop.py` (1,343 lines), model-free gates, verdict JSON per SHA, waves, model directive by complexity, Devin child prompts, cutting checklist. None of this is in the kit; the kit has `parallelize` (54 lines) and `sdd-to-card`. For the kit to speed up other repos (or a second collaborator), the architect→executor→reviewer flow needs to be kit content: a `process-loop` plugin with the orchestrator prompt, the issue template (`task.md`), the verdict schema, the proof allowlist and the rounds policy.

### 4.9 No measurement

The kit has no evals. `skill-creator` (vendor) brings an evals harness that has never been used. The only metric exists in the project (`ledger.csv`: rounds per PR, model, duration). Anthropic (skill evals, `claude plugin eval`) and market practice ("time to green", first-round approval rate, rework) ask that every rule change come with a before/after. Today the rule "session evidence before proposing" exists, but there is no baseline to know whether the change improved anything.

### 4.10 Small, but real

- `doctor.sh` enforces `read_config_from` on Devin to avoid loading `CLAUDE.md` twice; it is fragile machine configuration that a per-repository `CLAUDE.md` = `@AGENTS.md` would make unnecessary.
- `ci-godot.yml` exports Windows/macOS in a `barichello/godot-ci` Linux container, which the project had to patch (crash in `cowdata.h`, preset cache).
- `reviewer` creates worktrees (`git worktree add --detach`) and does not remove them; the project accumulated 53 worktrees and 61 orphan branches.
- The skill schema accepts lowercase `allowed-tools` (`read`, `exec`) and `agents/*.md` repeats the list in two formats; Claude Code uses `Read`, `Bash`. It is validated parity, but it doubles maintenance.
- `docs/projects.md` cites `platforms/install/` (removed in 8.0) and `knowledge/` (removed in 6.0).

## 5. What Anthropic, Cognition and the market prescribe today, and where the kit stands

The table summarizes the 2026 prescriptions and the kit's position. The full sources are in §9; two caveats: the Cognition site was blocked for the research agent (the texts came from search excerpts, with limits marked as "as reported"), and the Claude Code pages have no publication date, so I cite the Claude Code version that introduced each feature.

| Practice (source) | Kit today | Verdict |
|---|---|---|
| Instruction file under 200 lines; each line passes the test "would removing it cause an error?" (Claude Code `memory`, `best-practices`; blog "Steering Claude Code", 2026-06) | global `AGENTS.md` of 58 lines; project `AGENTS.md` of 22–69 lines | **correct** |
| `CLAUDE.md` is context, not enforced configuration; whatever must always hold goes into a `PreToolUse` hook (`best-practices`, `hooks`) | hook covers 5 patterns; skills promise "ask first" for dozens of operations without a hook | **partial** (§4.3) |
| Path-conditional rules in `.claude/rules/*.md` with `paths:`; rules without `paths` always load; path rules are summarized during compaction (`memory`, `context-window`) | 3 rules by glob, delivered by symlink in `~/.claude/rules/`; the content is only "load skill X" | **partial**: the rule should contain the constraints, not a pointer |
| `AGENTS.md` read natively since Claude Code 2.1.277 when there is no `CLAUDE.md`; `CLAUDE.md` with `@AGENTS.md` remains valid; Devin reads `AGENTS.md` in any folder (`memory#agents-md`; docs.devin.ai `agents-md`) | repos with only `AGENTS.md`; kit keeps `read_config_from` in Devin to avoid double loading | **correct**, but the `doctor.sh` workaround can be dropped |
| Skills: third-person description with triggers; body < 500 lines and < 5k tokens; references one level deep; `disable-model-invocation` removes the description from context; description+`when_to_use` truncated at 1,536 characters (`skills`; Agent Skills spec) | 43 skills, body ≤80 lines, 12 user-only, descriptions ≤160 characters | **correct** in format; **excess** in the number of model-invocable skills (§4.7) |
| Plugin: "an enabled plugin is part of every session"; split by concern so each repo enables only what it uses; `CLAUDE.md` at the plugin root **is not loaded** (`plugins/overview`, `plugins/create`) | 12 plugins, but all installed at user level via `all`; no repo declares `enabledPlugins` | **partial**: the split exists, the selective use does not |
| Cloud sessions and GitHub Action do not load local plugins; the Action reads `CLAUDE.md` on every run (`claude-code-on-the-web`, `github-actions`) | delivery by symlink on the machine | **wrong** for cloud (§4.2) |
| Verification: "if you cannot verify, do not ship"; `/goal`, Stop-hook gate, adversarial subagent that sees only the diff and the criteria; `/code-review`, `/verify` (`best-practices`) | `reviewer` re-runs proofs in a clean checkout; `validate-implementation` | **correct**; `/goal` and Stop-gate are missing in `sdd-implement` |
| Hooks: the current contract to deny in `PreToolUse` is `hookSpecificOutput.permissionDecision: "deny"`; exit 2 still blocks; `decision: block` is for PostToolUse/Stop (`hooks`) | hook uses `decision: block` + exit 2 | **works** via exit 2; the `hooks` doc marks `decision`/`block` as **deprecated** for PreToolUse |
| Official `security-guidance` plugin: pure hooks, extensible via `.claude/security-patterns.yaml` (≤50 rules) (`security-guidance`) | own hook as a one-line regex | **replaceable** by the official one + project rules |
| Evals before documenting: ≥3 cases per skill; `claude plugin eval` (2.1.269+) runs 3 times per case; most common finding: the description does not trigger (`plugin-evals`; `agent-skills/best-practices`) | no eval; `skill-creator` vendored and unused | **absent** (§4.9) |
| Multi-agent: single-threaded writes; extra agents contribute intelligence (research, review), not actions; "writer + independent reviewer" is the pattern that works (Cognition 2025-06 and 2026-04; Anthropic `sub-agents`, harness posts 2026) | `parallelize`, `researcher`, `reviewer`; DPRO-011 implements writer (Devin) + reviewer (Claude) | **correct**, but the loop lives outside the kit (§4.8) |
| Harness for long runs: feature list in JSON with `passes`, progress file, commits as checkpoints, "read git log + progress on start" (Anthropic 2025-11, 2026-03) | `session-handoff` in Markdown; task table in Markdown in the FEAT | **partial**: status in Markdown that nobody updates (§4.6) |
| Tasks for Devin: junior level, isolated, verifiable, ≤3 h; "What + How"; avoid design decisions without guidance; green confidence score doubles the chance of merge (docs.devin.ai; Devin 2.1) | `sdd-tasks` 5–30 min, ≤5 files, proof per task | **correct** (and stricter) |
| Devin Knowledge: the official page says "Knowledge is deprecated and will be removed in a future update", with automatic migration to skills in a "knowledge plugin" per scope (docs.devin.ai `knowledge`; probable date 2026-09-18 per release notes trackers); Playbooks remain documented and with an API (`creating-playbooks`, `playbook_id`) | Knowledge excluded; Playbooks excluded ("user-only skills cover it") | **correct** on Knowledge; **revisit** Playbooks: in Devin Cloud the loop's child receives a pasted prompt, which is exactly a Playbook |
| Devin plugins: `.devin-plugin/plugin.json` (only `name` required; `skills` is a path that replaces `skills/`), team meta-plugin, `requiredPlugins`/`optionalPlugins`/`forbiddenPlugins`; the plugin's `AGENTS.md` and `rules/` are always-on; **plugin subagents and hooks only load in Devin CLI/Desktop, not in the cloud**; "only one skill active at a time" in the product guide (docs.devin.ai `plugins/overview`, `cli/subagents`, `product-guides/skills`) | whole kit delivered by plugin; `researcher`/`reviewer`/hook declared local-only in the README | **correct** and well documented in the kit; a plan for what the cloud does not receive is missing |
| Devin environment: snapshot + `environment.yaml` (`initialize`, `maintenance`, `knowledge`); lint and tests ≤5 min each (docs.devin.ai `repo-setup`) | nothing in the kit | **absent** |
| Devin Review + autofix: reply only to `devin-ai-integration[bot]` to avoid loops (docs.devin.ai `devin-review-autofix`) | DPRO-011 does its own review by Claude | compatible; document the combination |
| Codex: the initial skills list is limited to ~2% of the context window, with 8,000 characters only when the window is unknown; `openai/codex#22078` (plugin skills not exposed) remains open (developers.openai.com `skills`; GitHub) | fixed budget of 7,200 characters; symlink fallback maintained by `doctor.sh` | **correct** in practice; the number is a floor, not the budget |
| Rule limits in Devin Desktop/Windsurf: `global_rules.md` 6,000 characters; each rule 12,000 (Windsurf docs, as reported) | `AGENTS.md` 4,335 characters | **correct** |
| Skills: Devin reads `.claude/skills/` and recommends `.agents/skills/`; Claude Code reads `.claude/skills/` (docs.devin.ai `skills`; Claude Code `skills`) | skills only in the plugin | **opportunity**: a versioned copy in `.claude/skills/` serves both |

### 5.1 Market: formats, empirical evidence and methodologies

| Practice (source) | Kit today | Verdict |
|---|---|---|
| `AGENTS.md` is the open standard (Agentic AI Foundation/Linux Foundation since 2025-12; read by Codex, Cursor, Copilot, Gemini CLI, Jules, Devin, Kiro, Zed and, since 2.1.277, Claude Code); the file closest to the code wins; Codex concatenates root→cwd with a 32 KiB cap (agents.md; developers.openai.com `agents-md`) | `AGENTS.md` per repo + global `plugins/core/AGENTS.md` via symlink | **correct**; nested `AGENTS.md` in `server/`/`client/` is missing only if it becomes a monorepo |
| Controlled study (Gloaguen et al., arXiv:2602.11988, 2026-02): **LLM-generated** context file reduces success by ≈3 p.p. and raises cost by >20%; **written by a dev** raises success by ≈4 p.p.; architecture prose "distracts into endless exploration", concrete commands help | the repos' `AGENTS.md` are hand-written, command-oriented and condition→action | **correct**; keep architecture overviews out of the always-on |
| arXiv:2601.20404 (2026-01): with `AGENTS.md`, median execution time −28.6% and output tokens −16.6%; IFScale (arXiv:2507.11538): adherence drops with instruction density and there is a primacy bias (what is at the top is followed more) | 58 lines, but the Truth/Skepticism section (abstract) comes before Boundaries (concrete) | **adjust** the order: Boundaries and Commands first |
| Rules per tool: Cursor `.cursor/rules/*.mdc` (`alwaysApply`/`globs`/description/manual, <500 lines); Copilot `.github/instructions/*.instructions.md` with `applyTo`; Kiro `.kiro/steering` with `fileMatch`; Claude `.claude/rules` with `paths` | only Claude and Devin (`globs`) | **adequate** for the scope; if Cursor/Copilot come in, generate with Ruler/rulesync instead of maintaining copies |
| One source, many targets: Ruler (`.ruler/AGENTS.md` → 30+ formats) and rulesync (70+ targets, imports from Claude Code) | `sync-project.sh` copies only the spec-lint | **opportunity**: `sync-project.sh` generating the per-tool files (A1) |
| SDD: "spec-first" (write and discard), "spec-anchored" (keep), "spec-as-source" (Böckeler/Thoughtworks 2025-10, 2026-02); Spec Kit criticized for "sea of markdown, rigid gates"; OpenSpec positions itself as lightweight | 10-step SDD with kept spec and manual status | **excess**: spec-anchored only for contracts (protocol, schemas, DECs); spec-first per task for the rest |
| "Write the learning back into the kit" (compound-engineering: one durable learning per run) | `session-review` proposes at most one change with evidence | **correct** |
| Autonomous loops (Ralph): a `PROMPT.md`/plan on disk, fresh context per iteration, backpressure from tests and CI, cost cap | DPRO-011 with model-free gates and `needs-human` after 2 rounds | **correct**, better than average |
| Godot: `godot --headless --import` before anything else; `gdlint`/`gdformat --check` (gdtoolkit 4.*); gdUnit4 headless with `--ignoreHeadlessMode` and JUnit XML, or GUT `-gexit -gjunit_xml_file`; `chickensoft-games/setup-godot` or `barichello/godot-ci`; commit `*.uid` (mandatory since 4.4), never `.godot/`; `godot-guard` detects 3.x syntax and invented APIs as a hook | kit: `--quit`, only GUT, no lint, no mention of `.uid` | **behind** (§4.4, D2–D4, N2) |
| Godot MCP: file servers are redundant with an agent that already has a shell; engine ones (run scene, read debugger) have value only in an interactive session, never in CI | kit excludes MCP ("`gh` covers it") | **correct** for CI; optional for interactive session |
| Godot multiplayer: default `@rpc` is `"authority"` (client calls are silently discarded), `"any_peer"` + server-side validation, identical node names on all peers, never Objects in RPC; "every new `@rpc` requires a server-side validation test" | project uses WebSocket + its own envelope (not `MultiplayerAPI`); kit covers neither | **absent** (N1) |
| Spring: Spring AI's own `AGENTS.md` is the model (exact commands, style, commit rules); `./mvnw -o verify` after `dependency:go-offline` for sandboxed agents; ArchUnit/Spring Modulith as a mechanical layer gate; Testcontainers with `@ServiceConnection` and containers as beans | server already has ArchUnit and Testcontainers; kit asks for `maven-enforcer`/ArchUnit | **correct**; the offline mode and the `@ServiceConnection` pattern are missing in the kit |
| Measure the kit as code: 20–50 representative tasks with deterministic verification, A/B of variants on the same commit and fixed model, run when `.claude/`, `AGENTS.md` or skills change; outcome metrics: PR acceptance, review discussion volume, rework (arXiv:2602.02345; DX AI Measurement Framework) | no eval; the loop's ledger exists | **absent** (N5) |

## 6. What to change in what already exists

Each item carries the reason, the change and the "done" criterion. The items are numbered for the plan in §8.

### A. Distribution: from the symlink on the machine to the commit in the repository

**A1. Each repository carries its own agent configuration.** `sync-project.sh` starts generating and maintaining (with `KIT_VERSION`, as it already does with `spec-lint/`):
- `CLAUDE.md` with one line `@AGENTS.md` (keeps `AGENTS.md` as the single source; guarantees the same content in older versions of Claude Code, in the GitHub Action and in cloud sessions);
- `.claude/settings.json` with `extraKnownMarketplaces` (the kit) and `enabledPlugins` **only with the plugins that repo uses**: client = `core`, `dev-core`, `dev-godot`, `quality-core`, `infra-github`; server = `core`, `dev-core`, `dev-java`, `infra-core`, `infra-persistence`, `quality-core`, `quality-security`, `infra-github`; docs = `core`, `architect-core`, `architect-sdd`, `quality-core`, `infra-github`;
- `.claude/rules/*.md` with the per-path rules **with real content** (see B2), not pointers;
- `.claude/skills/` with a versioned copy of the skills the repo uses, marked `.agent-rules-kit` as was already done in v6 (Claude Code and Devin read this directory; the Devin plugin remains the main path on Devin Cloud, and the copy covers Claude Code cloud sessions, the GitHub Action and collaborators without `bootstrap.sh`).

If Cursor or Copilot join the team, generate these files with Ruler or rulesync from the same `AGENTS.md` instead of writing the generator by hand. Done when: a clean clone, without `~/.ai-kit`, in Claude Code web or on a runner, loads the same rules and skills as the owner's machine; `sync-project.sh --check` runs in the CI of the three repos and fails on divergence.

**A2. Remove machine facts from the kit.** `godot-4-versions.md`, `java-25-lts.md`, `docs/maintenance.md` stop saying "installed on this machine". The project's pinned versions live in the repo's `AGENTS.md` (they already do: 4.7.2, Java 25, Boot 4.1) and in Devin's `environment.yaml` (item C3). Absolute paths `/Users/christian/...` leave `ARCHITECT.md`, `config.json`, `.devin/config.json` and prompts, replaced by paths relative to the clone or environment variables.

**A3. Freeze the layout.** Declare 10.x stable (no path changes) for one quarter; content changes are MINOR/PATCH. Add to `check_kit.py` a "cited paths" gate that scans the consumer repos (via `sync-project.sh --check <repo>`) looking for `agents/skills/`, `rules/godot/`, `kits/java-maven/`, `platforms/install/`, `knowledge/` and fails. Fix the obsolete citations in `stratics-docs/AGENTS.md:20`, `DTEC-001`, `DTEC-002` and in the kit's `docs/projects.md`.

### B. Always-on content and rules

**B1. Resolve the 98% vs. "decide and proceed" contradiction.** Replace § Skepticism with three verifiable lines: (1) a claim without a source is a hypothesis and is marked as such; (2) ambiguity that does not block → decide, state the assumption in one line, proceed; (3) a real block → one question with 2–4 options and a recommendation. The "98%" number goes: it is not measurable and Anthropic recommends instructions the model can verify.

**B2. Per-path rules with content.** `plugins/dev-godot/rules/godot.md` starts containing the 8–12 constraints that most avoid rework in `.gd`/`.tscn` (mandatory typing, never `get_parent()` for game rules, `.uid`/`*.import` travel with the file, never edit `.godot/`, boot-proof with `grep 'SCRIPT ERROR'`, mandatory gdUnit4 test for new logic, 4.x syntax: `@onready`/`@export`/`await`/`instantiate()`), and the same for `java.md` (JdbcClient without JPA when the project decides so, `Clock`/`RandomGenerator` injected into the domain, ArchUnit, a new migration is never edited). The long skill keeps existing for the "how", the rule carries the "never/always". Reason: a per-path rule costs zero until the file is touched and survives the flow without requiring the model to invoke the skill.

**B3. Reorder and add two lines to the global `AGENTS.md`.** Put Boundaries (Always/Ask/Never) and Session at the top and Truth/Skepticism after: the IFScale study shows primacy bias, and the concrete sections are the ones that prevent incidents. Add: "When compacting, preserve the list of modified files and the test commands" (official guidance for `context-window`) and "Task scope = the issue's `Files` cell; a path outside it → stop and name it" (today only in the project's `CONTRIBUTING.md`, it is the rule that saved the most rounds).

### C. Hooks, verification and security

**C1. Guard hook: cover what the skills promise or stop promising.** Recommended option: enable the official `security-guidance` plugin (pure hooks, maintained by Anthropic) and register the project's rules in `.claude/security-patterns.yaml`; keep the kit's hook only for what the official one does not cover. Minimal option: extend the regex to `rm -r -f`/`--recursive --force`, `find -delete`, `git push +ref`/`:ref`, `git branch -D`, `git checkout -- .`/`git restore .`, `git stash drop|clear`, `docker compose down -v`, `docker system prune`, `flyway:clean`, `git filter-repo`, `git lfs migrate`, `gh repo delete`; switch the output to `hookSpecificOutput.permissionDecision: "deny"`; add the 25 cases from the assessment session to `hook_guard_cases.json`. Done when: every "Ask first"/"Never" in `AGENTS.md` and in the skills has either a hook, or the sentence "there is no hook; it depends on the instruction".

**C2. Formatting and lint hooks.** `PostToolUse` on `Edit|Write`: `gdformat`/`gdlint` (gdtoolkit) for `*.gd`, `spotless:apply` (or `google-java-format` directly, faster) for `*.java`, `check_spec.py` for `docs/spec/**`. It is Anthropic's number one example for hooks and eliminates the "formatting" finding class from reviews.

**C3. Verification inside `sdd-implement`.** End each task with `/goal "<task proof> passes"` (or a Stop-hook that runs the proof) and, for a visual change, require a screenshot/GIF. Include worktree cleanup in `reviewer`/`validate-implementation` (`git worktree remove`; `git worktree prune`) so as not to repeat the 53 orphaned worktrees.

### D. Godot: remove the wrong advice and add the missing advice

**D1. Movement and physics stop being the default.** `godot-standards` and the template start saying: "the movement model is a project decision (`AGENTS.md`/DGME); physics (`CharacterBody2D`) **or** tile stepping; never both". The health component example remains valid.

**D2. Tests: gdUnit4 as the default, GUT as the alternative, never skip silently.** `ci-godot.yml` fails if the runner is absent and requires "N test cases" > 0 in the output (the project's `reusable-ci-godot.yml` already does this: promote it to the kit); emit JUnit XML for the PR; ready-made alternative: `godot-gdunit-labs/gdUnit4-action` with `warnings-as-errors`. Coverage policy for GDScript: "every game rule in a pure class tested without `SceneTree`; no numeric gate" (mutation testing does not exist for GDScript).

**D3. Correct boot-proof.** Replace `godot --headless --quit` with `godot --headless --import` (the official documentation: imports all resources and exits; `--headless` is mandatory without a GPU) followed by `! godot --headless --path . --quit 2>&1 | grep -q 'SCRIPT ERROR'` in `godot-standards`, `validate-implementation`, `reviewer` and in the CI template (ARCHITECT.md delta 6).

**D4. Generated files are part of the task.** `sdd-tasks` pre-cut already requires it; the per-path rule (B2) and the client's PR template start listing `*.uid`, `*.import`, `*.translation`.

### E. SDD: less ceremony, derived state, project deltas absorbed

**E0. Two spec regimes.** Adopt the Thoughtworks distinction: **spec-anchored** (maintained and validated) only for what is a contract between repos and people: `protocol/`, content schemas, DECs, REQs and journeys; **spec-first** (written, used for cutting and then frozen as history) for FEATs and tasks. This removes the obligation to keep 52 FEATs alive and concentrates the effort where a mistake costs two teams.

**E1. Derived status, not typed.** Remove the obligation to edit task and FEAT `status` by hand. `spec_trace.py` (already exists in `stratics-docs/tools/spec-trace`) or `project-sync` start deriving: issue closed by a merged PR → task `done`; all tasks `done` → FEAT `delivered`; generate `traceability.md` and update the frontmatter in an automatic PR. Promote `spec_trace.py` to the kit (`platforms/ci/validations/`), as DPRO-013 already proposes.

**E2. `sdd-tasks` and `sdd-to-card` absorb deltas 1–5 from `ARCHITECT.md`.** One issue per task (title `[FEAT-NNN Tn] ...`), columns `Complexity | Model | Wave`, the `task.md` issue template as the canonical format, waves with disjoint files, model directive by complexity. `sdd-implement` describes the real flow: worktree per issue, PR per task, `Closes <owner>/<docs-repo>#N`, merge by the reviewer.

**E3. Prototype lane.** A game needs to iterate on "feel" (movement, camera, battle feedback) before specifying. Create `sdd-spike`: a `spike/<topic>` branch with a deadline (≤2 days), no coverage gate, whose only deliverable is a video/GIF and a proposed DGME; the spike's code is discarded or re-implemented via SDD. This avoids specifying 9k lines before there is a character walking on the screen.

**E4. Cut steps without demonstrated value.** `sdd-analyze` and `sdd-audit` can become a single mechanical check (`check_spec.py` + a 10-item checklist) executed by the `researcher`; two steps of 50 lines each for FEATs of 100 lines is the "spec theater" that Thoughtworks and the Spec Kit authors themselves warn about.

### F. Skills: fewer, sharper

**F1. Consolidate.** `clean-code` + `simplicity` → `code-standards`; `clean-architecture` + `ddd-and-patterns` → `architecture`; `sessions` + `session-review` + `session-handoff` → `session` (with `/session handoff`). From 43 to ~30 skills, ~22 model-invocable. Reason: Devin Cloud activates one skill at a time (according to the kit itself) and Anthropic warns that the model chooses among "100+ skills" by description; overlap reduces accuracy.

**F2. Move to an optional plugin (`extras`)**: `frontend-design`, `find-skills`, `krita`, `dbeaver`, `skill-creator` (the last one is useful for the maintainer, not for the executor). None of them helps implement a Stratics task; `find-skills` also encourages installing third-party skills by popularity.

**F3. `tokens` without compression levels.** Keep the three registers (technical, human, governed); remove `lite/full/ultra`. Output compression does not reduce input tokens (where the cost is) and conflicts with the pt-BR/governed rule.

### G. Java/Spring

**G1. Update the facts**: `project-agents-java-spring.md` template to Java 25 + Boot 4.x, `pom-parent.xml` to the current BOM (3.5.x left OSS support on 2026-06-30; the GA line is 4.1.1), `java-25-lts.md` without "on this machine". **G2.** Add `references/jdbcclient-flyway.md` (the JPA-free pattern the project adopted: `JdbcClient`, explicit mapping, injected `Clock`, idempotency via `command_receipts`) and `references/archunit-rules.md` with the `ArchitectureTest` rule set as a template. **G3.** Testcontainers with `@ServiceConnection` and containers as beans (the Boot docs warn that a static `@Container` fights with the `ApplicationContext` cache), `reuse` and the `-Pfast` profile documented in the server's `AGENTS.md` to keep "tests ≤5 min"; `./mvnw -o verify` after `dependency:go-offline` in the `environment.yaml`/snapshot for agents in a sandbox without network.

## 7. What to include (new)

**N1. The `dev-godot` plugin gains 2D online game `references/`** (or a `dev-godot-netplay` plugin, dependent on `dev-godot`):
- `authority-and-prediction.md`: the server decides; the client sends intent, predicts ≤1 step, reconciles on `move_rejected`; never game rules on the client; `BattleEvents` queue consumed in order.
- `network-codec.md`: JSON envelope, `protocol_version`, `WebSocketPeer` with heartbeat and reconnection, valid/invalid fixtures from `protocol/examples` tested on the client.
- `testable-game-logic.md`: state in pure `RefCounted`, injected `Clock`/RNG, gdUnit4 without a scene, scene runner only for integration, `--ignoreHeadlessMode`.
- `gdscript-4-pitfalls.md`: the short list of what the model gets wrong (`onready var`→`@onready`, `export`→`@export`, `yield`→`await`, `instance()`→`instantiate()`, `KinematicBody2D`→`CharacterBody2D`, `TileMap`→`TileMapLayer`, `connect("sig", ...)`→`sig.connect(...)`), with the instruction "when in doubt, open the class at `docs.godotengine.org/en/4.x/classes/`".
- `scenes-and-generated-files.md`: `.uid`, `*.import`, `.translation`, conflicts in `.tscn`, UIDs, what never to edit by hand.
- `performance-budget.md`: frame target, nodes per scene, pooling, generated `TileMapLayer`, Nearest textures.

**N2. Godot tooling in the CI kit**: `gdtoolkit` (`gdlint`/`gdformat`) with a default `gdlintrc`, pinned version (`gdtoolkit==4.*`), a job in `ci-godot.yml`, and the C2 hook; evaluate `godot-guard` (detects 3.x syntax and nonexistent APIs; runs as a hook/pre-commit) as `PostToolUse` on `*.gd`; commit `*.uid` and forbid manual editing of generated `.uid`/`.tscn`. Optional and experimental: `lspServers` in the plugin pointing to the Godot editor's LSP for `.gd`.

**N3. Real Devin in the kit**: `environment.yaml` template (`initialize`: Godot 4.7.2 headless, JDK 25, Maven offline; `maintenance`: `./mvnw -q dependency:go-offline`, `godot --headless --import`; `knowledge`: the DoD commands), snapshot checklist, and **Playbooks** `*.devin.md` for "implement issue" and "fix round" (today they are `devin-child-implement.md`/`devin-child-fix.md` outside the kit, pasted by hand into Devin). Since plugin subagents and hooks do not load on Devin Cloud and only one skill is active at a time, the plugin's `AGENTS.md` and the per-glob `rules/` are what the cloud child actually receives: the critical constraints (B2) need to be in them, not only in the skills. Document the DPRO-011 + Devin Review autofix combination with an allowlist only for `devin-ai-integration[bot]`.

**N4. `process-loop` plugin** with what DPRO-011 has already proven: parameterized orchestrator prompt (no absolute paths), verdict schema, proof allowlist, round policy (2 rounds → `needs-human`), ledger and the batch report. It is the highest-leverage content for a second project or a second collaborator.

**N5. Evals and metrics**: `evals/evals.json` with ≥3 cases for the 8 most used skills (`godot-standards`, `java-standards`, `sdd-tasks`, `validate-implementation`, `reviewer`, `protocol-contract`, `investigate`, `skeptic`), `claude plugin eval` in the kit's CI (fixed model), and a `platforms/tools/kpi.py` that reads `ledger.csv` and publishes per batch: first-round approval rate, rounds per PR, findings with `owner: spec`, time to green. Suggested target for the next month: first pass approved ≥60% (today 39%) and spec findings ≤25%.

**N6. Harness for long runs** (Anthropic 2025-11/2026-03): per FEAT under implementation, a `progress.json` with the tasks and `passes: true|false` (JSON is less improperly edited by the model than Markdown), read at the start of each session together with `git log`; replaces the manual status in the FEAT for the executor.

**N7. `REVIEW.md` per repo** (if the Team/Enterprise plan with hosted Code Review is used) with the criteria that today are in `doc-review-checklist.md`, and `/code-review` as a step of `validate-implementation` in Claude Code.

## 8. Prioritized plan

| Phase | Items | Effort | Expected effect |
|---|---|---|---|
| **Week 1** (without changing layout) | A3 (freeze + path gate), B1, D1, D2, D3, C1 (extend hook or `security-guidance`), E2 (deltas 1–5 to the kit), fix obsolete citations in the repos | 2–3 days | eliminates contradictory advice in every `.gd`; hook covers what it promises; the described process is the process used |
| **Weeks 2–3** | A1 (sync generates `CLAUDE.md`, `settings.json`, `rules/`, `skills/`), A2, B2, B3, C2, E1 (derived status), F1–F3, G1–G3 | 4–6 days | kit works in cloud, Action and on a new machine; fewer skills and more accuracy; reliable spec status |
| **Month** | N1–N3, E3 (spike lane), E4, C3, N4, N5, N6 | 2 weeks | 2D online game content in the kit; Devin with environment and Playbooks; reusable loop; metrics to know whether it improved |

What **not** to change: the size of `AGENTS.md`, schema validation, the vendor lock, the requirement of proof re-executed in a clean checkout, the claim classes and the habit of only changing the kit with session evidence.

How to measure whether it worked: compare two loop batches before and after Week 1 (`ledger.csv`): first-round approval, rounds per PR, share of `spec` findings. If Week 1 does not move these numbers, the hypothesis that the kit's contradictions cost rounds is refuted and the focus should go only to task cutting (E1/E2).

## 9. Sources, evidence and limits of this assessment

### 9.1 Local evidence (reproducible)

```bash
# kit validator and manifests (both pass on 10.1.0)
CI=1 python3 platforms/ci/validations/check_kit.py
claude plugin validate plugins/core && claude plugin validate .

# description budget and AGENTS.md size
python3 - <<'PY'
import re,glob;print(sum(len(re.search(r'^description:\s*(.*)$',open(f).read(),re.M).group(1).strip().strip('"')) for f in glob.glob('plugins/*/skills/*/SKILL.md')))
PY
wc -lc plugins/core/AGENTS.md

# guard hook: commands that pass without being blocked (24 of 25)
CMD="$(python3 -c "import json;print(json.load(open('plugins/core/hooks/hooks.json'))['hooks']['PreToolUse'][0]['hooks'][0]['command'])")"
for c in "rm -r -f build" "git push origin +main" "git restore ." "docker compose down -v" "./mvnw flyway:clean"; do
  printf '{"tool_name":"Bash","tool_input":{"command":"%s"}}' "$c" | bash -c "$CMD" >/dev/null 2>&1 && echo "allowed  $c" || echo "BLOCKED  $c"
done
```

Project facts cited: `stratics-docs/docs/spec/decisions/DPRO-011-orchestrated-review-loop.md:132` (20 of 33 PRs rejected), `docs/spec/ARCHITECT.md` deltas 5–6, `CONTRIBUTING.md:122-168`, `ops/review-loop/README.md` (lessons), `docs/spec/spec.md:13,62`, task tables of the FEATs (128 `todo`/3 `done`), `stratics-docs/AGENTS.md:20`, `DTEC-001:19,43`, `DTEC-002:50`, `stratics-server/pom.xml:7-12` (Boot 4.1.1), `stratics-client/project.godot` (4.7, Mobile, gdUnit4).

### 9.2 Fact check on the kit's premises (2026-10-06)

| Kit premise | Verdict | Source |
|---|---|---|
| Devin has plugins with `.devin-plugin/plugin.json`, `devin plugins install owner/repo[#path]`, team meta-plugin | confirmed | docs.devin.ai `cli/extensibility/plugins/overview`, `product-guides/plugin-ecosystem` |
| The plugin's `AGENTS.md` and `rules/` are always-on; `triggers: [user]` = slash only; `subagent:`/`agent:` in the skill frontmatter | confirmed | docs.devin.ai `plugins/overview`, `cli/subagents`, `skills/creating-skills` |
| Plugin hooks and subagents only in Devin CLI/Desktop; `hooks.json` compatible with Claude Code; "best effort, fail open" | confirmed | docs.devin.ai `cli/extensibility/hooks/overview` |
| Devin Cloud: one active skill at a time | confirmed (product guide) | docs.devin.ai `product-guides/skills` |
| "Cognition deprecated Knowledge" | confirmed ("Knowledge is deprecated and will be removed… migrated to Skills in Plugins"); Playbooks remain supported | docs.devin.ai `product-guides/knowledge`, `creating-playbooks` |
| `read_config_from` in `~/.config/devin/config.json`; `~/.agents/skills` | confirmed (keys: `agents_standard, cursor, windsurf, claude, opencode, vscode, zed`) | docs.devin.ai `cli/reference/configuration/read-config-from` |
| Codex: marketplace `.agents/plugins/marketplace.json`, `codex plugin add x@mkt`, `agents/openai.yaml` `allow_implicit_invocation` | confirmed | `openai/codex` (codex-rs/cli, core-plugins, skills) |
| Codex: ~8,000 characters for the skills list | partial: ~2% of the context window; 8,000 only when the window is unknown | developers.openai.com `codex/skills` |
| `openai/codex#22078` open | confirmed (open since 2026-05-11) | GitHub |
| Claude Code: `~/.claude/rules/` and `.claude/rules/` with `paths:` | confirmed | code.claude.com `memory` |
| Claude Code reads `AGENTS.md` natively | confirmed since 2.1.277, only when there is no `CLAUDE.md` above the cwd | code.claude.com `memory#agents-md` |
| `dependencies`, `renames`, `category` in manifests | confirmed | code.claude.com `plugins/manifest-reference`, `marketplace-reference` |
| `/doctor prompt-audit`, `/context` | confirmed (prompt-audit ≥2.1.283) | code.claude.com `commands` |
| PreToolUse hook with `decision: block` | **deprecated**; use `hookSpecificOutput.permissionDecision: deny`; exit 2 still blocks | code.claude.com `hooks` |
| Current Claude Code | 2.1.290 (2026-10-05) | changelog; npm |
| Godot 4.7.2 is the latest stable; `barichello/godot-ci:4.7.2` exists; `TileMapLayer` since 4.3; GUT 9.7.1 for 4.7.x; gdUnit4 6.2.1 up to 4.7.1 in the table | confirmed | GitHub godotengine, Docker Hub, bitwes/Gut, MikeSchulze/gdUnit4 |
| Java 25 LTS (GA 2025-09-16); Spring Boot GA 4.1.1; 3.5.x out of OSS support since 2026-06-30 | confirmed | oracle.com, spring.io, Maven Central |
| Agent Skills spec: `name` ≤64, `description` ≤1024, body < 500 lines; Devin and Windsurf are not listed in the client showcase | confirmed | agentskills/agentskills `specification.mdx` |

### 9.3 External sources

**Anthropic / Claude Code** (accessed on 2026-10-06): code.claude.com/docs/en/{memory, best-practices, features-overview, skills, hooks, hooks-guide, sub-agents, plugins/overview, plugins/create, plugins/manifest-reference, plugins/marketplace-reference, plugin-evals, commands, model-config, mcp, context-window, worktrees, claude-code-on-the-web, github-actions, code-review, security-guidance, claude-security, changelog}; platform.claude.com/docs/en/agents-and-tools/agent-skills/{overview, best-practices}; claude.com/blog/steering-claude-code-skills-hooks-rules-subagents-and-more (2026-06-18); anthropic.com/engineering/{building-effective-agents 2024-12, multi-agent-research-system 2025-06, writing-tools-for-agents 2025-09, effective-context-engineering-for-ai-agents 2025-09, equipping-agents-for-the-real-world-with-agent-skills 2025-10, effective-harnesses-for-long-running-agents 2025-11, demystifying-evals-for-ai-agents 2026-01, building-c-compiler 2026-02, harness-design-long-running-apps 2026-03, claude-code-auto-mode 2026-03, managed-agents 2026-04}.

**Cognition / Devin** (site blocked for the research agent; text taken from search excerpts and from the pages confirmed in the fact check): cognition.ai/blog/dont-build-multi-agents (2025-06-12); cognition.com/blog/multi-agents-working (2026-04-22); devin-annual-performance-review-2025 (2025-11-14); devin-2-1 (2025-05); introducing-devin-2-2 (2026-02-24); closing-the-agent-loop-devin-autofixes-review-comments (2026-02-10); testing-development (2026-05-29); devin-can-now-manage-devins (2026-03-19); docs.devin.ai/{essential-guidelines/when-to-use-devin, essential-guidelines/instructing-devin-effectively, onboard-devin/agents-md, onboard-devin/repo-setup, product-guides/knowledge, product-guides/creating-playbooks, product-guides/skills, product-guides/plugins, product-guides/plugin-ecosystem, product-guides/session-insights, work-with-devin/devin-review, use-cases/gallery/devin-review-autofix, cli/extensibility/{plugins/overview, rules, skills/creating-skills, hooks/overview}, cli/subagents, cli/reference/configuration/read-config-from}.

**Market** (many primary domains blocked for the agent; the GitHub repositories of the same docs and converging secondary sources were used, marked in the research report): agents.md and github.com/agentsmd/agents.md; developers.openai.com/codex/guides/agents-md; cursor.com/docs/context/rules; github.com/github/docs (custom-instructions-support.md); github.com/google-gemini/gemini-cli (gemini-md.md); kiro.dev/docs/steering; github.com/intellectronica/ruler; github.com/dyoshikawa/rulesync; arXiv:2602.11988 (Gloaguen et al., 2026-02), 2601.20404 (2026-01), 2511.12884 (2025-11), 2602.02345 (2026-02), 2507.11538 (IFScale, 2025-07), 2307.03172 (Lost in the Middle); coderabbit.ai "State of AI vs Human Code Generation" (2025-12-17); github.com/humanlayer/advanced-context-engineering-for-coding-agents and 12-factor-agents; martinfowler.com (Böckeler, "Understanding SDD" 2025-10; "Context Engineering for Coding Agents" 2026-02-05); github.com/github/spec-kit; github.com/Fission-AI/OpenSpec; github.com/obra/superpowers; github.com/EveryInc/compound-engineering-plugin; github.com/ghuntley/how-to-ralph-wiggum; github.com/addyosmani/agent-skills and addyosmani.com/blog/agentic-code-quality (2026-08-12); simonwillison.net/guides/agentic-engineering-patterns; Godot: github.com/godotengine/godot (CHANGELOG 4.4–4.7), godot-docs (command_line_tutorial, upgrading_to_godot_4.6, gdscript_basics), godotengine.org/article/uid-changes-coming-to-godot-4-4, github.com/Scony/godot-gdscript-toolkit, github.com/MikeSchulze/gdUnit4 and gdUnit4-action, github.com/bitwes/Gut, github.com/chickensoft-games/setup-godot, github.com/abarichello/godot-ci, github.com/brocolriri/godot-guard, github.com/Coding-Solo/godot-mcp, gamedev-skills/awesome-gamedev-agent-skills (godot-multiplayer); Spring: github.com/spring-projects/spring-ai (AGENTS.md), spring-boot (testcontainers.adoc), spring-modulith, TNG/ArchUnit; measurement: getdx.com AI Measurement Framework, developertoolkit.ai (evals in CI).

### 9.4 Limits

- Nothing was executed against Devin or Codex in the assessment session; the claims about them come from documentation.
- The "61% rejected" measurement is the project's own (DPRO-011); it was not recalculated from GitHub.
- The Cognition report used in the synthesis was out of date about Knowledge; table 9.2 prevails where there is a conflict.
- The rule limit numbers for Windsurf/Devin Desktop (6,000/12,000 characters) came from excerpts and were not verified on the page.
