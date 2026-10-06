# P2-02 — Path-scoped rules carry real constraints, not pointers

Phase: 2 · Repos: kit (agent-rules-kit) · Branch to create: feat/p2-02-path-rules-with-content from main · Depends on: P1-04, P1-05, P1-06 · Effort: ~3 h

## Goal

Rewrite the three glob-triggered rules (`plugins/dev-godot/rules/godot.md`, `plugins/dev-java/rules/java.md`, `plugins/architect-sdd/rules/spec.md`) so that each carries its 8-12 highest-value always/never constraints inline, in at most 40 body lines, with exactly one pointer line to the owning skill for procedures. Raise the validator's rule body limit from 12 to 40 lines so the gate still runs. Measurable result: a Devin Cloud child or a Claude Code session that touches a `.gd`, `.java` or `docs/spec/**/*.md` file receives the constraints without invoking any skill; today it receives one sentence telling it which skill to load.

## Why

- assessment §5 (rules row): "3 rules by glob ... content is only 'load skill X'"; verdict "partial: the rule should contain the constraints, not a pointer".
- assessment §6 B2: a path rule costs zero context until the file is touched and survives the flow without the model invoking a skill; the skill keeps the "how", the rule carries the "never/always".
- assessment §7 N3 (last sentence): on Devin Cloud, plugin subagents and hooks do not load and only one skill is active at a time, so the plugin `AGENTS.md` and the glob `rules/` are what the cloud child actually receives; the critical constraints must live there.
- assessment §4.5: the client rules that avoid rework (non-authoritative client, typed GDScript, generated files, Godot 3 syntax as a failure mode) exist only in the Stratics client `AGENTS.md` (stratics-client `AGENTS.md:38-48`, `:52-53`, `:62`), not in the kit.
- kit `platforms/ci/validations/check_kit.py:28` caps a rule body at 12 lines, which is why the rules degenerated into pointers; the three bodies today are two text lines each (3 counted by `body_line_count`, which includes the blank line after `---`).
- Claude Code summarizes path-scoped rules away on compaction, so each line must be short and imperative to survive as a summary.

## Current state

kit `plugins/dev-godot/rules/godot.md` (15 lines; body = lines 14-15):

```
plugins/dev-godot/rules/godot.md:2: description: Load Godot 2D standards, Clean Code, and testing guidance for Godot project files.
plugins/dev-godot/rules/godot.md:14: Load skill `godot-standards`; it points to `clean-code` and `testing`.
plugins/dev-godot/rules/godot.md:15: Apply their guidance to matching Godot files.
```

kit `plugins/dev-java/rules/java.md` (13 lines; body = lines 12-13):

```
plugins/dev-java/rules/java.md:2: description: Load Java standards, Clean Code, and testing guidance for Java and Maven files.
plugins/dev-java/rules/java.md:12: Load skill `java-standards`; it points to `clean-code` and `testing`.
plugins/dev-java/rules/java.md:13: Maven is required; use the fixed Java LTS.
```

kit `plugins/architect-sdd/rules/spec.md` (11 lines; body = lines 10-11):

```
plugins/architect-sdd/rules/spec.md:2: description: Load governed specification templates and SDD skills for files under docs/spec.
plugins/architect-sdd/rules/spec.md:10: Governed documents: use `templates/spec-*.md` and the `sdd-*` skills.
plugins/architect-sdd/rules/spec.md:11: Never compress these documents.
```

Frontmatter of all three already uses `trigger: glob` and `globs`/`paths` as YAML sequences (`godot.md:3-11`, `java.md:3-9`, `spec.md:3-7`); keep them byte-for-byte.

kit `platforms/ci/validations/check_kit.py`:

```
platforms/ci/validations/check_kit.py:28: RULE_BODY_MAX_LINES = 12
platforms/ci/validations/check_kit.py:673:         if body_lines > RULE_BODY_MAX_LINES:
platforms/ci/validations/check_kit.py:674:             fail(rel(rule_file), f"body has {body_lines} lines (>{RULE_BODY_MAX_LINES})")
```

kit `INDEX.md` "Plugin rules" table:

```
INDEX.md:38: | File | Trigger | Globs | Loads |
INDEX.md:40: | [`plugins/dev-java/rules/java.md`](plugins/dev-java/rules/java.md) | `glob` | `**/*.java`, `**/pom.xml` | `java-standards`, `clean-code`, `testing` |
INDEX.md:41: | [`plugins/dev-godot/rules/godot.md`](plugins/dev-godot/rules/godot.md) | `glob` | `**/*.gd`, `**/*.tscn`, `**/project.godot` | `godot-standards`, `clean-code`, `testing` |
INDEX.md:42: | [`plugins/architect-sdd/rules/spec.md`](plugins/architect-sdd/rules/spec.md) | `glob` | `docs/spec/**/*.md` | SDD skills and spec templates |
```

kit `docs/maintenance.md:13` (rule row of the "Type | Steps" table) starts with: `| rule | create `plugins/<plugin>/rules/<name>.md` in the owning plugin with `description`, `trigger: glob|model_decision|manual`, and `globs` for a glob rule; ...` and says nothing about the body.

Plugin indexes list the rules by file name only (`plugins/dev-godot/INDEX.md:12`, `plugins/dev-java/INDEX.md:10`, `plugins/architect-sdd/INDEX.md:18`, each `- <name>.md`); file names do not change, so these files are not edited.

Sources for the constraints (read before writing): stratics-client `AGENTS.md:38-48` (typed GDScript, `@onready`, signals/EventBus, tile-step, BattleEvents), `:52-53` (`.tscn` text diff, never `.godot/`, always `*.import`), `:62` (never `get_parent()`, never authoritative rules on the client); stratics-server `AGENTS.md:8` (JdbcClient, no JPA), `:41` (constructor injection), `:47` (injected `Clock`/RNG, ArchUnit), `:61-64` (new migration always, editing an applied one is ask-first there and becomes Never here per assessment §6 B2, never `@Disabled`); kit `plugins/architect-sdd/skills/sdd-constitution/references/sdd-process.md:41` (id namespaces, "never reuse") and `:45` (claim tags); kit `plugins/dev-godot/skills/godot-standards/SKILL.md:45` (boot proof as corrected by P1-06; if P1-06 is not merged yet, use the command below verbatim anyway).

## Change

1. kit `platforms/ci/validations/check_kit.py:28`: change `RULE_BODY_MAX_LINES = 12` to `RULE_BODY_MAX_LINES = 40`. No other validator change.
2. kit `plugins/dev-godot/rules/godot.md`: keep lines 3-12 (trigger, globs, paths and the closing `---`) unchanged; replace line 2 and the body with:

```
description: Always/never constraints for GDScript, scenes and project.godot; procedures stay in skill godot-standards.
```

```
Always/never for `*.gd`, `*.tscn` and `project.godot`. Procedures: skill `godot-standards` (names: `clean-code`; test gates: `testing`).

- Always: Godot 4 syntax only: `@onready`, `@export`, `await`, `instantiate()`, `signal_name.connect(callable)`. Never `onready var`, `export`, `yield`, `instance()`, `connect("name", ...)`.
- Always: typed GDScript: `var speed: float = 120.0`, `func hit(dmg: int) -> void`; an untyped variable, parameter or return is a defect.
- Never: `get_parent()` or an ancestor lookup to apply a game rule; use signals or the project's `EventBus` autoload.
- Never: `$Node` or `get_node` inside `_process`/`_physics_process`; cache the node in an `@onready` declaration.
- Always: the movement model is the one the repo `AGENTS.md` declares (tile-step or physics); never mix both in one entity.
- Never: an authoritative game rule on the client; the client sends intent, predicts only what the repo `AGENTS.md` allows and reconciles on the server's answer.
- Always: new or changed logic ships with a gdUnit4 test under `tests/` (GUT only when the repo `AGENTS.md` says so); testable logic lives in a `RefCounted` class that needs no scene.
- Always: `.uid`, `*.import` and `.translation` files travel with their source in the same commit and in the task's `Files` cell.
- Never: edit `.godot/`, a `.uid` file or a generated `*.import` by hand; regenerate with `godot --headless --path . --import`.
- Always: `.tscn`/`.tres` are text: read the diff; resolve a UID conflict by reimport, never by editing the UID.
- Always: boot proof before "done": `godot --headless --path . --import` then `! godot --headless --path . --quit 2>&1 | grep -q 'SCRIPT ERROR'`; paste the literal output.
```

3. kit `plugins/dev-java/rules/java.md`: keep lines 3-10 (trigger, globs, paths and the closing `---`) unchanged; new description `Always/never constraints for Java and Maven files; procedures stay in skill java-standards.`; body of 10-12 bullets in the same `- Always:`/`- Never:` form, one pointer line to `java-standards` first, covering exactly: Maven wrapper `./mvnw` at the LTS the repo fixes, never global `mvn`/Gradle/PATH JDK; no framework import (`org.springframework`, `jakarta.persistence`, `java.sql`) in `domain/`, the ArchUnit gate fails it; never `Instant.now()`, `LocalDate.now()`, `new Random()`, `Math.random()` in `domain/`, inject `java.time.Clock` and `java.util.random.RandomGenerator` ports; constructor injection, `final` class, `private final` fields, never field `@Autowired`; `record` for DTOs, `@ConfigurationProperties` and value carriers, a persistence entity never crosses the adapter boundary; `Optional` only as a return type; never edit an applied Flyway migration, schema change = new `V<n+1>__<slug>.sql` under `src/main/resources/db/migration/`; persistence style follows the repo `AGENTS.md` (`JdbcClient` + hand-written SQL, or JPA), never introduce the other one; domain tests are pure JUnit 5 + AssertJ without `@SpringBootTest`, Mockito only at ports; never `@Disabled` to go green, `ddl-auto=update`, or a secret in `application*.yml`; `./mvnw spotless:check verify` green before a PR with the literal tail pasted. Do not state a Java or Spring version number (P2-12 owns facts).
4. kit `plugins/architect-sdd/rules/spec.md`: keep lines 3-8 (trigger, globs, paths and the closing `---`) unchanged; new description `Always/never constraints for governed documents under docs/spec; procedures stay in the sdd-* skills.`; body of 8-10 bullets, pointer line to the `sdd-*` skills and `sdd-constitution/references/sdd-process.md` first, covering exactly: start from the governed template (`spec-feature.md`, `spec-requirement-functional.md`, `spec-requirement-non-functional.md`, `spec-decision.md`, `spec-debt.md`, `spec-index.md`) and keep every section; never compress, summarize or drop a section; ids namespaced and sequential (`FEAT-nnn`, `REQ-F-nnn`, `REQ-NF-nnn`, `DTEC-nnn`/`DGME-nnn`/`DPRO-nnn`, `DEBT-nnn`), file name carries the id, never reuse a retired id; every claim carries one of `[FACT]` (with source), `[DECISION]`, `[PROPOSAL]`, `[HYPOTHESIS]`, `[BLOCKER]`, an untagged assertion counts as `[HYPOTHESIS]` (both the tag list and the untagged-assertion clause on the same bullet line); a FEAT lists its REQs and each REQ lists that FEAT (one-sided links fail `check_spec.py`); never edit a `status` field by hand when the repo's tooling derives it from GitHub, otherwise only the architect edits it and the PR says why; prose and frontmatter in English, dates `YYYY-MM-DD`; open only the FEAT/REQ/DEC/DEBT files the task cites, orient with `docs/spec/spec.md`, never bulk-read the corpus; run the project spec gates (`check_spec.py`, `spec_trace.py check` when present) and paste the literal result.
5. kit `INDEX.md:40-42`: keep the table columns; replace the three Loads cells (inner skill names in backticks, nothing else in the cell). Loads cell for java.md becomes exactly: inline always/never; procedures in `java-standards`, `clean-code`, `testing`. Loads cell for godot.md becomes exactly: inline always/never; procedures in `godot-standards`, `clean-code`, `testing`. Loads cell for spec.md becomes exactly: inline always/never; procedures in the `sdd-*` skills and spec templates.
6. kit `docs/maintenance.md:13`: after `and `globs` for a glob rule;` insert `body = one pointer line to the owning skill plus 8-12 always/never bullets, at most 40 lines;`.
7. kit `CHANGELOG.md` under `## [Unreleased]` / `### Changed`: one entry (what, why with assessment §6 B2 and §7 N3, proof = the acceptance commands below).
8. Every rule line is one sentence, imperative, with no "see skill" except the pointer line; no absolute path, no machine name, no Stratics-specific id (FEAT/DTEC numbers stay in the project `AGENTS.md`).

## Out of scope

- Movement-model wording in `godot-standards` and the Godot template: P1-04. gdUnit4 default and CI policy: P1-05. The boot proof text in `SKILL.md:45` and `platforms/kits/github/workflows/ci-godot.yml`: P1-06.
- `plugins/core/AGENTS.md` ordering or new lines: P2-03. Generating `.claude/rules` per project: P2-05. Format/lint hooks: P2-07.
- Java/Spring version facts and references: P2-12, P2-13. Godot references (authority, codec, pitfalls): P3-01. Status derivation tooling: P2-08.
- No new rule files, no glob changes, no change to `doctor.sh` or `smoke.sh` symlink logic, no change to `rule.schema.json`.
- Skill renames (`clean-code` -> `code-standards`): P2-09. If P2-09 has already merged (`ls plugins/*/skills | grep -c code-standards` prints 1), write `code-standards` instead of `clean-code` in the two pointer lines (steps 2-3) and the two INDEX.md Loads cells (step 5); do not reintroduce `clean-code`.

## Acceptance criteria

- [ ] `grep -c 'RULE_BODY_MAX_LINES = 40' platforms/ci/validations/check_kit.py` prints `1`; `grep -c 'RULE_BODY_MAX_LINES = 12' platforms/ci/validations/check_kit.py` prints `0`.
- [ ] `grep -c 'Load skill' plugins/*/rules/*.md` prints `0` for each of the three files.
- [ ] For each rule: `n=$(grep -c '^- \(Always\|Never\):' <file>)` is between 8 and 12; `awk '/^---$/{n++; next} n>=2{c++} END{print c+0}' <file>` prints at most 40 (lines after the closing `---`, the same count as `body_line_count` in `check_kit.py:163-168`).
- [ ] `python3 -c "import yaml,sys;[print(len(yaml.safe_load(open(p).read().split('---')[1])['description'])) for p in sys.argv[1:]]" plugins/dev-godot/rules/godot.md plugins/dev-java/rules/java.md plugins/architect-sdd/rules/spec.md` prints three numbers, each at most 160.
- [ ] `grep -c "SCRIPT ERROR" plugins/dev-godot/rules/godot.md` prints `1`; `grep -c 'onready var' plugins/dev-godot/rules/godot.md` prints `1` (listed as forbidden).
- [ ] `grep -c 'RandomGenerator' plugins/dev-java/rules/java.md` prints `1`; `grep -c 'V<n+1>__' plugins/dev-java/rules/java.md` prints `1`; `grep -cE 'Java 2[0-9]|Spring Boot [0-9]' plugins/dev-java/rules/java.md` prints `0`.
- [ ] `grep -c '\[HYPOTHESIS\]' plugins/architect-sdd/rules/spec.md` prints `1`; `grep -c 'DGME' plugins/architect-sdd/rules/spec.md` prints `1`.
- [ ] `grep -c 'inline always/never' INDEX.md` prints `3`; `grep -c 'at most 40 lines' docs/maintenance.md` prints `1`.
- [ ] `grep -rnE '^(globs|paths): ' plugins/*/rules/*.md` prints nothing (sequences only, no inline string).
- [ ] `grep -cE 'FEAT-[0-9]|DTEC-[0-9]{3}|DPRO-[0-9]{3}' plugins/dev-godot/rules/godot.md plugins/dev-java/rules/java.md` prints `0` for both; `grep -cE '(^|[ (])/[A-Za-z]' plugins/*/rules/*.md` prints `0` for each (no absolute path).
- [ ] Gates, each with its literal last line pasted in the PR: `platforms/tools/check.sh` prints a line starting `check: OK (`; on a machine without the `claude` CLI its last line is `check: claude plugin validate skipped (claude not in PATH)`, which is fine. `platforms/tools/smoke.sh` ends with a line starting `smoke: OK (`. `python3 -B -m unittest discover -s platforms/ci/validations -p "test_*.py"` ends `OK`. `python3 platforms/ci/validations/check_kit.py --links` prints `3 rules` and no FAIL line naming a path under `plugins/`, `platforms/`, `INDEX.md`, `docs/maintenance.md` or `CHANGELOG.md`; FAIL lines under `docs/plans/` are pre-existing and out of scope (report them under `unverified`; while any exist, `check_kit.py` exits 1 and its summary line, and therefore `check.sh`'s, reads `check: failed (` instead of `check: OK (`, which is the same pre-existing condition, not a regression of this task).
- [ ] `git diff --stat main` lists exactly: the three rule files, `platforms/ci/validations/check_kit.py`, `INDEX.md`, `docs/maintenance.md`, `CHANGELOG.md`; `VERSION` untouched.

## Conventions

- Everything committed is in English; plain ASCII punctuation in the new rule lines.
- No layout or path change: the 10.x layout is frozen; rules stay at `plugins/<plugin>/rules/<name>.md`; no file is added to a `rules/` folder (Devin loads every `.md` there as a rule, `check_kit.py:654`).
- `VERSION` untouched; `CHANGELOG.md` gets a `## [Unreleased]` entry with what, why and proof.
- INDEX.md of every touched folder lists every entry by name: the root `INDEX.md` rules table is updated (step 5); plugin indexes already list the unchanged file names.
- Rule frontmatter = `description` at most 160 chars + `trigger: glob` + `globs` and `paths` as YAML sequences equal to each other (`check_kit.py:671`); Devin rejects a comma-separated string.
- `plugins/core/AGENTS.md` is not touched (at most 60 lines, header `# Global Rules — AI Kit`); always-on content lives only there, so nothing in a rule may claim to apply outside its globs.
- Keep the Claude Code gotcha in mind: path-scoped rules are summarized on compaction; one constraint per line, no paragraphs, no examples longer than one expression.
- Commit: Conventional Commits, e.g. `feat(rules): carry always/never constraints inline in path-scoped rules` with `Refs: docs/plans/2026-10-kit-assessment/assessment.md §6 B2, §7 N3`.
- PR body = What / Why / How I tested (literal output of the four gates) / Refs.
- Executor may be Devin or Claude Code; nothing here needs a Claude-only tool.

## Report back

Final message format: `done` (every file path edited, each gate command with its literal last line) · `unverified` (anything not run, e.g. a Godot or Maven command on a machine without the toolchain, which is expected: this task runs no Godot or Maven) · `next step` (P2-05 generates `.claude/rules` from these files; P1-06 and P1-04 merge order if they landed after this branch).

Proposed CHANGELOG line (under `### Changed`): `- Path-scoped rules (`godot.md`, `java.md`, `spec.md`) carry 8-12 inline always/never constraints and one pointer to the owning skill; `RULE_BODY_MAX_LINES` 12 to 40. Evidence: assessment §6 B2 and §7 N3; a Devin Cloud child receives only `AGENTS.md` and glob rules, and the three bodies were two pointer lines each. Proof: `check.sh`, `smoke.sh`, unit tests and `check_kit.py --links` green.`
