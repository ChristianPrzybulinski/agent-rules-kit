---
id: KIT-059
title: "The path rules change after the owner's rule-by-rule review"
status: confirmed
confirmed: "2026-11-12 (owner, chat of the kit always-on review session: \"Sim, linha always-on\" (yes, the always-on line) for Codex reach; then \"tome suas recomendacoes como aceitas ate segunda ordem\" (take your recommendations as accepted until further notice) for the java, godot, spec and python items and for the proposal from the owner's links, which asked for rules for java, godot, python, spec and json, \"criando as que nao existem\" (creating the ones that do not exist))"
issue: ""
pr: ""
---

# KIT-059 — The path rules change after the owner's rule-by-rule review

## Problem and evidence

[FACT] On 2026-11-12, after KIT-058, the owner reviewed the four path rules of `plugins/guardrails/rules/` (`godot`,
`java`, `python`, `spec`) one at a time, in the KIT-057 format: what each does, an example, its origin, who enforces
it, the risk without it, and a recommendation set against its 2 strongest alternatives.

### Codex reach (all four rules): one always-on line

[FACT] Claude Code attaches a rule by its `paths` from the repository's `.claude/rules/`, and Devin loads it by its
`globs` from the plugin; Codex loads no rule by glob, and the README platform table called its path rules
"description routing". The 318 local Codex rollouts (2026-11-04 to 2026-11-12) opened a rule file in a shell command
twice (`.claude/rules/dev-godot-godot.md` and `.claude/rules/dev-java-java.md`), but read `client/AGENTS.md` by command
in 120 rollouts and `server/AGENTS.md` in 49, because the Stratics root `AGENTS.md` names them ("Governed by
`client/AGENTS.md`"). The Stratics review loop does not hand rules to its workers: on `origin/main`,
`.claude/rules` appears under `platform/review-loop` only in a test inventory line and a test fixture. So the rule
bullets no skill repeats (typed GDScript, `.uid` travel, `@SuppressWarnings`, the whole Python rule) reached the main
implementer nowhere. A pointer in each Stratics folder `AGENTS.md` would be repeated per repository and break on the
next rule rename (`core-*` to `guardrails-*` in 12.0.0); a block written by `sync-project.sh` would make the sync a
writer of a human-owned file. The owner chose the always-on line. It is wrong if, after the change, fewer than half of
the Codex rollouts that edit a `.gd`, `.java` or `.py` file read the matching rule, or Claude Code sessions re-read a
rule already attached more than once per session on average.

### java: the PR gate defers to the repository, applied migrations are ask-first

[FACT] `rules/java.md` said "Always: `./mvnw spotless:check verify` green before a PR". The Stratics
`server/AGENTS.md` (`origin/main`, lines 37-38) makes `./mvnw -B -ntp spotless:check test-compile` the gate before a
commit or PR and runs the full `spotless:check verify` "once per batch on main", "not a pre-push gate"; the repository
file wins, but the rule attached to every `.java` edit stated the opposite. The rule also said "Never: edit an applied
Flyway migration" and `skills/persistence/SKILL.md` "never edit an applied migration", while the always-on Boundaries
(KIT-057) put "changing an applied migration" under **Ask first**: three owners, two answers. The rule loaded 173 times
in 75 Claude Code sessions (2026-10-08 to 2026-11-12, `nested_memory` attachments). Keeping both lines relies on
precedence and leaves a rule line agents learn to ignore; deleting the gate line loses the default for a repository
that names no gate. It is wrong if Stratics PRs that touch only `.java` files pass the smoke but fail the full `verify`
on `main` more than once a batch; then the repository file, not the rule, should change.

### godot, spec and python: kept

[FACT] `rules/godot.md` loaded 227 times in 118 sessions and is the only edit-time reminder of typed GDScript: the
Stratics `client/.gdlintrc` sets line length and returns only, and `client/project.godot` sets no untyped-declaration
warning. `rules/spec.md` is the most loaded rule (321 loads, 119 sessions) and its gates exist in Stratics
(`check_spec.py`, `spec_trace.py check`). `rules/python.md` (KIT-045, 2026-11-11) loaded twice in one session; it is
re-measured on 2026-12-12 (wrong if it has under 10 loads then, or Python PRs still show bare `except`, unnamed `noqa` or
`shell=True` after it loaded). A typing gate for the Stratics client is a project change, not a kit one.

### The owner's links: a json rule and two rule lines

[FACT] The owner then sent 57 links (Java, Godot, Python, spec-driven development, JSON, architecture, DDD, testing,
agent practice, DORA) and asked for a proposal for the java, godot, python, spec and json rules, creating the missing
ones, with Devin, Codex and Claude Code as the consumers. Every link was read: a plain fetch first, then a browser for
the 24 that answered HTTP 403 or an empty page; 3 stayed partial behind a paywall. Most of what they recommend the kit
already says; the full assessment, including the skill additions left for the skills review, is in the PR body. The
rule changes:

- json, new, for the profiles `godot java python docs`. Stratics `origin/main` tracks 31,429 JSON files, among them a
  33,441,147-byte `game/content/packs/pilot/manifest.json`, generated protocol tables checked by
  `platform/tools/protocol-gen/gen.py --check --all`, and schema checks in `content-check` and `protocol-check`
  (`.github/workflows/docs-checks.yml`). Claude Code transcripts hold 94 Edit or Write calls on `.json` files in 37
  sessions; the rest went through scripts. The web sources gave only generic formatting advice, so the bullets come from
  these repositories: keep the format and key order, no duplicate key, edit by script, never read a huge file whole,
  never hand-edit generated JSON, validate against the schema, `$schema` and `$id`, stable ids. It is wrong if the rule
  loads on JSON edits and agents still hand-edit generated JSON or read a pack whole.
- godot: the official Godot best-practices page on scene organization has a child report up by signal and its parent
  call down; the `get_parent()` bullet also names a sibling path.
- java: a broad `catch` that goes on silently is now named. Stratics `server/src/main` holds 46 broad catches; the ones
  read sit at a connection loop or a schedule and log the exception, which the bullet keeps allowed.

Not adopted, with the evidence against: "never `Optional.get()`" (21 Stratics lines call it after a presence check),
"never `datetime.utcnow()`" (no use in Stratics Python, 62 calls use `datetime.now(timezone.utc)` or an equivalent),
and "never read input in `_process`" (the Godot page on notifications discourages it for performance, not as an error).

## Change

`plugins/guardrails/AGENTS.md`, Boundaries: the `**Always**` line reads "read the repo's `AGENTS.md` and README before
changing it, and before editing a file, each `.claude/rules/*.md` whose `paths` match it unless it is already in your
context; run the checks the change's impact requires (skill `testing` § 6) before saying \"done\"." (58 lines,
6,346 → 6,460 bytes). The README platform table says Codex reads path rules from the repository's `.claude/rules/` on
that line, and `docs/design.md` explains why.

`plugins/guardrails/rules/java.md`: "Always: a schema change is a new `V<n+1>__<slug>.sql` under
`src/main/resources/db/migration/`; editing an applied migration is ask-first (`AGENTS.md` Boundaries)." replaces the
Flyway "Never", and "Always: before a PR, the build gate the repo `AGENTS.md` names green (`./mvnw spotless:check verify`
when it names none), with the literal tail pasted as proof." replaces the fixed gate. `skills/persistence/SKILL.md`
says "editing an applied migration is ask-first (`AGENTS.md` Boundaries)".

`plugins/guardrails/rules/json.md` (new, `**/*.json`, 8 bullets) and its line in `platforms/tools/sync-profiles.txt`
(`godot java python docs`); `rules/godot.md`: "Never: `get_parent()`, an ancestor lookup or a sibling path
(`$\"../Other\"`) to apply a game rule; a child reports up by signal and its parent calls down, or use the project's
`EventBus` autoload."; `rules/java.md`: "Never: catch `Exception`, `Throwable` or `RuntimeException` and go on silently;
catch the narrowest type and keep the cause (`throw new X(..., e)`); a broad catch stays only where a failure must not
stop a connection, loop or schedule, logged with the exception as the last argument." The README names the JSON rule;
`plugins/guardrails/INDEX.md` is regenerated. `platforms/ci/validations/test_sync_project.py` expects
`guardrails-json.md` in a multi-profile sync and checks that it keeps `**/*.json` when the `docs` profile covers the
root; the previous expectation failed on the new rule.

## Proof

`bash platforms/tools/check.sh`, `CI=1 bash platforms/tools/check.sh`, `bash platforms/tools/smoke.sh`,
`python3 platforms/ci/validations/check_kit.py --links`, `python3 platforms/tools/gen_index.py --check`,
`python3 -B -m unittest discover -s platforms/ci/validations -p "test_*.py"` and
`gitleaks git --redact --log-opts=origin/main..HEAD`; results in the PR body.

## History

- 2026-11-12: confirmed (owner, chat, rule by rule).
