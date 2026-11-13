---
id: KIT-061
title: "The skills change after the owner's skill-by-skill review"
status: confirmed
confirmed: "2026-11-13 (owner, chat of the kit review session: one answer per item, from \"Sim, aplicar\" for java-standards to \"Sim, fechar\" for the five skills kept as they are; the proposal from the owner's 57 links was accepted on 2026-11-12 with \"tome suas recomendacoes como aceitas ate segunda ordem\" (take your recommendations as accepted until further notice) and reviewed item by item here)"
issue: "#213"
pr: ""
---

# KIT-061 — The skills change after the owner's skill-by-skill review

## Problem and evidence

[FACT] After KIT-057 (always-on), KIT-058 (hooks) and KIT-059 (path rules), the owner reviewed the 27 skills of
`plugins/guardrails/skills/` on 2026-11-13, one item at a time, in the KIT-057 format: what it is, an example, origin
and evidence, who enforces it, the risk without it, the recommendation against its 2 strongest alternatives and what
would prove it wrong. The skill additions B1–B10 of the proposal built from the owner's 57 links (2026-11-12) went
through the same review. Every line cited was re-read on `origin/main` `19607f3` and Stratics `stratics-docs`
`origin/main` `52277530c` (2026-11-13) before it was presented.

Usage figures come from the read-only scans of 2026-11-12: 1,232 Claude Code sessions (2026-10-03 to 2026-11-13 UTC) and
318 Codex rollouts (2026-11-04 to 2026-11-12). Codex read `testing` in 312, `session` in 305 and `code-standards` in
278 of them; Claude Code loaded kit skills through the `Skill` tool in at most 6 sessions each. A rule that must reach
Codex therefore belongs in a skill it reads or in `AGENTS.md`.

### Items that change

1. `java-standards`: `SKILL.md:53` and `references/build-and-dependencies.md:45` made `./mvnw -o -q spotless:check verify`
   the task step; Stratics `server/AGENTS.md:37-38` makes `spotless:check test-compile` the gate before a commit or PR
   and the full `verify` "not a pre-push gate". Same fix as `rules/java.md` in KIT-059.
2. `sdd-journey`: its one `Skill` call (2026-10-06) was refused because it was user-only, while Stratics holds 64
   journeys in `docs/spec/journeys/`, still edited on 2026-11-13. It becomes model-invocable; its description names a
   J-NN journey instead of "a user-visible flow", so a UI task does not load it.
3. `sdd-constitution`: `references/sdd-process.md:14` said `implement → validate` after KIT-039 renamed the step to
   `review`. `STALE_KIT_PATHS` (`sync-project.sh:253`) says it covers layouts 1.x to 11.x but missed `plugins/sdd/`,
   `plugins/dev/` and `plugins/architect-`, so Stratics `AGENTS.md:33` still cites
   `plugins/sdd/skills/sdd-constitution/references/sdd-process.md`. A `git grep` with the scan's regex and exclusions on
   Stratics finds 6 lines in 3 files that the existing pattern already flags (`plugins/core/`, added by KIT-055 after
   Stratics' last sync `0124899`) and 8 more lines in 4 files for the new names; `sync-project.sh --check` itself was
   not run on Stratics.
4. `docker` and `persistence`: `docker/SKILL.md:18` and `persistence/references/postgres-18.md:16` cited
   `platforms/kits/docker/compose.yml`, which exists in no consumer repository (Stratics has 6 Compose files of its
   own). `docker/SKILL.md:42` asked first for `docker compose down -v` and `postgres-18.md:15` told the agent to run it,
   while the guard hook denies it to agents (`hook_guard_cases.json`, `blocked`). `docker/SKILL.md:47` repeated `:24`.
5. `session`: three `start` lines restated `AGENTS.md` (§ Session and § Work loop) in other words; its plan threshold
   ("containing ambiguity") differed from `AGENTS.md`'s ("a spec's should/probably, a bug with no named root cause").
6. `code-standards` (79 of 80 lines): `:63` repeated the `AGENTS.md` Scope line and `:77`'s last clause repeated
   `AGENTS.md` § Truth and `references/living-docs.md:50`.
7. `git`: `:32` allowed a co-author footer "only if the project requires it"; no kit or Stratics file requires one,
   yet the last 20 commits carry 73 (kit) and 60 (Stratics) `Co-Authored-By: Claude` lines, which the harness adds.
8. `investigate` runs as a fork (`context: fork`), so the caller sees only its description; `AGENTS.md` § Work loop
   sends the third failure to it without saying what to pass. `review/references/claim-check.md:8` already tells its
   caller to pass context.
9. `sdd-tasks`: `:39` allowed a shared wave only for disjoint file sets, while its own
   `references/waves-and-models.md:11` and Stratics `ARCHITECT.md:44` allow shared files after a clean `git merge-tree`
   replay.
10. `sdd-clarify`: `:23` asked up to five questions in one call; the owner dismissed 2- and 4-question prompts and
    answered single ones at once (memory `owner-question-style`, 2026-10-07/08), `AGENTS.md` § Decisions asks one
    question, and `AskUserQuestion` takes at most 4 per call.
11. `sdd-implement`: `:48` listed the PR body sections that `references/task-pr.md:29` also lists.
12. `sdd-specify`: KIT-004 (confirmed 2026-10-07, issue #75 closed, `pr: ""`) was never shipped; `:42` named
    `platforms/tools/check.sh --spec`, a kit-only path. Stratics already has id gaps (FEAT-087 to 089, 10 in `J`) and
    `check_spec.py` has no sequence rule, so a reserved unused id passes.
13. `krita`: 0 `Skill` calls, 0 slash commands, 0 Codex reads; Stratics holds no `.kra`; `:25` and `:29` cited paths no
    consumer has; `make_spritesheet.py` writes frames, size, order and sha256, not the pivot `:29` promised.
14. `grilling`: pinned at `mattpocock/skills` `d81f3a1` (2026-09-30); upstream `7739eae` (2026-10-29, equal to `main`
    on 2026-11-13 for this skill) differs by two text lines, read as data before the fetch; `agents/openai.yaml` and
    the MIT license are unchanged.
15. `testing` (B1, B3, B4): a feature's failing test was required but never run or recorded; `:57` caught only the
    empty-return case; nothing asked for independent tests (Stratics has no random-order setting).
16. `review` (B10, detection half of B2): `agents/reviewer.md` step 4 holds the risk categories and the weakened-check
    list, but no local Codex rollout mentions `agents/reviewer.md` (0 of 308), so for Codex the skill had neither the
    categories nor a check for a loosened assertion. Its proof paragraph, which repeats the profile's step 2, stays as
    Codex's only copy.
17. `architecture` (B7): `AGENTS.md` § Decisions asks on "a real blocker" without saying which choices block; nothing
    stopped new code from copying an existing break; the Strategy row named no lighter form. Sources: Srinath Perera,
    the skillsdirectory architecture skill, the refactoring.guru criticism page; no Stratics incident behind them.
18. `godot-standards` (B8): `:45` set no limit on an autoload; no line chose between `RefCounted`, `Resource` and
    `Node`, routed gameplay input, or named the `add_child` and `@export` preload pitfalls. Stratics has 7 autoloads,
    26 `_input` and 3 `_unhandled_input` handlers (not read one by one) and 0 `@export ... = preload(`. Sources: the
    official Godot best-practices pages; `logic_preferences.html` re-read on 2026-11-13.
19. `protocol-contract` (B9, narrowed): Stratics `platform/tools/protocol-gen/gen.py` "Emits constant tables only
    (never message classes or validators)", checked by `gen.py --check --all` in `docs-checks.yml:132`;
    `code-standards:63` already routes generated files through their generator. § 5 named no regeneration step.

### Items kept as they are

- `security`: no secret scan in the `review` fallback gates. Stratics' loop gate runs `gitleaks git` over every PR's
  commits (`platform/review-loop/loop.py:3259`, FEAT-053 T76) and the kit runs it locally before each PR; `review` is
  at its 80-line cap. Wrong if a secret reaches a pushed commit in a reviewed PR or a second consumer has no secret gate.
- `parallelize`, `sdd-check`, `sdd-plan`, `sdd-spike` (dormant: 0 spikes; re-check on 2027-01-01), `sdd-to-card`: no
  defect found; none contradicts a change above.
- `persistence`: its applied-migration line changed in KIT-059; the rest moves with item 4.

### Not adopted

- B2 as a rule in `testing`: `AGENTS.md` § Boundaries already forbids weakening a test and `testing` § 5 forbids
  disabling one; only its detection half went to `review`.
- B5 (mutation runs exclude test, generated and third-party code): Stratics PIT targets the changed classes
  (`targetClasses` = `${scoped.quality.mutation-classes}` in `server/pom.xml`) and `gd_mutation.py` mutates changed
  functions only.
- B6 (a course correction goes to the record): `session/SKILL.md:25` already keeps each decision or correction in the
  issue, PR or handoff record, and Codex reads `session` in 305 of 318 rollouts; `sdd-implement` is user-only.
- B9 as written ("consumer types ... never hand-write them"): wrong for Stratics, which hand-writes message classes by
  design.

## Change

- `plugins/guardrails/AGENTS.md` § Work loop: "A third failure → stop and report the attempts and premises, or load
  skill `investigate` with the symptom, each attempt's failing output and the shared premise." (58 lines.)
- `java-standards/SKILL.md:53`: "Run the build gate the repo `AGENTS.md` names with the Maven wrapper
  (`./mvnw spotless:check verify` when it names none; module gates and offline flags in the build reference)."; its
  build reference's task step is "the gate the repo `AGENTS.md` names, with `-o`".
- `sdd-journey`: `triggers` adds `model`, `disable-model-invocation` goes, `agents/openai.yaml` allows implicit
  invocation; description "Use when writing or changing a J-NN journey."
- `sdd-constitution/references/sdd-process.md`: `implement → review`, and the KIT-004 sentence verbatim ("When two or
  more spec sessions run against one specification at the same time, each session's prompt reserves a block of ids
  for every kind it may create ...; a session takes ids only from its own block. A reserved id left unused stays a gap
  and is never reused."). `platforms/tools/sync-project.sh` `STALE_KIT_PATHS` adds `plugins/sdd/`, `plugins/dev/` and
  `plugins/architect-`; `test_sync_project.py` adds `test_11x_plugin_layouts_fail` (fails with the previous pattern,
  `0 != 1`) and `test_current_plugin_layout_passes`.
- `docker/SKILL.md`: "Edit the repository's own Compose file; a repository without one starts from
  `~/.ai-kit/platforms/kits/docker/compose.yml`."; "`docker compose down -v` destroys data; the user runs it (the guard
  hook blocks it for agents)."; the `.env.example` line of § 5 goes. `persistence/references/postgres-18.md` asks the
  user to run `docker compose down -v` and cites the repository's own Compose file.
- `session/SKILL.md` `start`: "When the outcome sentence (`AGENTS.md` § Session) cannot be written, ask before
  proceeding." and "When `AGENTS.md` § Work loop calls for a plan, propose planning mode before editing; once a plan is
  approved, execute it without reopening it."; the new-topic sentence goes.
- `code-standards/SKILL.md`: the drive-by refactor line and the code-wins clause go (79 → 78 lines).
- `git/SKILL.md`: "No AI attribution in the title; a co-author footer follows the project's or the agent platform's
  attribution setting."
- `sdd-tasks/SKILL.md`: "Waves: `references/waves-and-models.md` (wave 0, shared files, cross-FEAT order); ...".
- `sdd-clarify/SKILL.md`: "Ask at most five per round, one question per call of the runtime's ask tool ...; each has
  one-line context with a concrete example, ...".
- `sdd-implement/SKILL.md`: "open a PR whose body follows `references/task-pr.md` (last line
  `Closes <owner>/<docs-repo>#N`)".
- `sdd-specify/SKILL.md`: the first unused id of a block the session prompt reserves, `REQ` ids included; "Run the
  project spec validator (`python3 .github/spec-lint/check_spec.py docs/spec .github/spec-lint/schemas`; in this kit,
  `platforms/tools/check.sh --spec docs/spec`)."
- `krita/` removed with its `sync-profiles.txt` line and `INDEX.md` row; `sync-project.sh` removes a vendored copy on
  the next sync. `asset-import`: description "Not for drawing or retouching art."; § 4 gains the
  `~/.ai-kit/platforms/kits/godot/scripts/make_spritesheet.py <frames-dir> <output.png>` step, which writes
  `<output.png>.manifest.json`, with the pivot recorded in the batch manifest.
- `grilling`: `skills.lock` pins `7739eaed7f8f3915437a8def198a6d0d7206dbc7`, verified 2026-11-13; `vendor.sh` rewrote
  `SKILL.md` and `VENDOR.md`.
- `testing/SKILL.md` (72 → 74 lines): a feature's test is written and run before the implementation exists and its
  failing line goes to the PR's Proof; a test that passes when the rule it names is removed proves nothing; a test
  pins only what the spec or task asked for (characterization excepted); each test builds and removes its own data
  and passes alone and in any order.
- `review/SKILL.md` (80 lines): changed files are read in risk order (security, input validation, control flow, public
  interfaces) and changed code no test exercises is reported; the diff of every test file is read, and a dropped count,
  a deleted or skipped test or a loosened assertion the PR does not name is a weakened check.
- `architecture/SKILL.md` (62 → 66 lines): "Before building on a choice that is expensive to reverse (protocol or
  public API shape, schema, framework, external integration, auth model), propose a DEC and ask; decide a reversible
  choice yourself and go."; "When the code you extend already breaks these rules, new code does not copy the break:
  isolate it behind a seam or follow the rules in the new part, and name the existing break in the PR as a follow-up;
  refactoring it needs the task's scope."; the Strategy row of `references/pattern-catalog.md` starts with a function
  value.
- `godot-standards/SKILL.md` (56 → 58 lines): dependencies through `@export` or a `Callable` the parent sets; gameplay
  reads discrete input in `_unhandled_input`, `_input` serves a handler that must see an event before the GUI; a new
  autoload only for a self-contained system; `RefCounted`, `Resource` or `Node` by need. `references/gdscript-4-pitfalls.md`
  gains the `add_child` and `@export` preload rows and cites `logic_preferences.html`.
- `protocol-contract/SKILL.md` § 5: "regenerate every file the project generates from the protocol with its generator
  and run the generator's `--check`".
- `plugins/guardrails/INDEX.md` regenerated; KIT-004 recorded as done.

Stratics follow-ups (outside the kit): on the next sync to 12.x, `AGENTS.md:33` cites
`.claude/skills/sdd-constitution/references/sdd-process.md` and 13 historical lines get `<!-- kit-path-ok -->`, 2 of
them in DPRO-015 (an owner edit); DPRO-006:50 cites `plugins/infra-core/skills/git-lfs/...`, which no scan catches (an
owner edit); `platform/review-loop/loop.py:6377` tells a spec child to use `sdd-tasks`, which it cannot load.

## Proof

`bash platforms/tools/check.sh`, `CI=1 bash platforms/tools/check.sh`, `bash platforms/tools/smoke.sh`,
`python3 platforms/ci/validations/check_kit.py --links`, `python3 platforms/tools/gen_index.py --check`,
`bash platforms/tools/vendor.sh --check`,
`python3 -B -m unittest discover -s platforms/ci/validations -p "test_*.py"` and
`gitleaks git --redact --log-opts=origin/main..HEAD`; results in the PR body. Not run: `claude plugin eval` (billed);
`CONTRIBUTING.md` § Evals reruns a case when one of its eight skills changes its `description`, and the two descriptions
that changed (`sdd-journey`, `asset-import`) have no case.

## History

- 2026-11-13: confirmed (owner, chat, item by item).
