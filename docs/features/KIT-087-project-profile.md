---
id: KIT-087
title: "One project profile, .ai-kit.yaml, read only by the kit's skills, hooks and actions"
status: in-progress
confirmed: "2026-11-16 (owner, chat of the kit session: \"sim abre a 087\", detailed with \"Sim, detalhe\"; the six decisions of #322: \"concordo com as 6\")"
issue: "#322"
pr: ""
---

# KIT-087 — One project profile, .ai-kit.yaml, read only by the kit's skills, hooks and actions

The owner's principle (2026-11-16): a project never calls a kit script directly; a kit skill reads the project's
profile, its own settings, and does what is needed. CI, which runs no skill, uses the kit's composite actions. The
profile holds only parameters the kit reads; another tool's settings (a review loop's config) stay in its own files
(owner, 2026-11-16).

## Problem and evidence

[FACT] From the inventory behind #322 (kit at `be62ae9`), re-read on `origin/main` `0b4b0c5`:

1. **One fact, many homes.** The folder-to-stack map lives in the `CLAUDE.md` sync marker (`sync-project.sh`
   `claude_profile`), `sdd.components` and `sdd.rule_paths`; protected paths in `sdd.protected_paths` and the gates
   JSON's `protected_paths`, in two shapes.
2. **Four homes, four parsers.** The `sdd:` frontmatter (`check_spec.py`), the gates JSON (`pr_gates.py --config`),
   the marker regex in `sync-project.sh` and the spec-tools action inputs.
3. **No home for non-SDD settings.** CI trigger policy, changelog mode, test commands, coverage policy and the secret
   scanner's config have no key; the kit's templates and the consumer contradict each other on CI triggers.
4. **Precedent.** The `sdd:` block already behaves as a profile: 23 keys, a schema, defaults, `--params`, unknown keys
   refused with or without pyyaml.

## Change

Four phases, one PR each, plus P1b, the kit's own profile (#322):

- **P1 — schema and dual-read resolver (MINOR): done in #327 (c85e381).**
  1. `platforms/ci/schemas/profile.schema.json`: a top-level `kit` pin (`">=X.Y"`, checked against `VERSION`) and the
     sections `stacks`, `sdd` (the 23 keys of `spec.schema.json`, `journeys` nullable, plus `task_cut` and
     `decision_folding` for KIT-086), `tracker` (labels limited to the two `spec_trace.py` reads), `models`, `tests`,
     `quality`, `evidence`, `review`, `gates` (only the keys kit tools read: `owner`, `issue_repo`, `repos` with
     `require_fragment`, `protected_paths`, `proof_allowlist`, `generated_neighbours`, `expected_red_checks`),
     `changelog`, `ci` (`trigger` defaults to `dispatch`) and `secrets`. Every key has a default and one `x-read-by`
     phase (session, sdd, implement, review, delivery, security); unknown keys fail; `x-<name>` keys at the top level
     or directly in a section are ignored.
  2. `platforms/tools/profile.py resolve [--section S] [--json] [--file F] [ROOT]`: standard library, Python 3.9; it
     parses with `check_spec.py`'s `load_yaml` (pyyaml, else its fallback parser) and checks with its `check_value`,
     which gains `patternProperties` and `maximum`. It reads `<git top>/.ai-kit.yaml`, then per key the legacy homes:
     the `sdd:` block (checked against `spec.schema.json` as before), the root `CLAUDE.md` marker (`stacks`) and the
     gates JSON `sdd.row_checks.gates` names (`gates`, `backlog_repo` read as `issue_repo`), each with
     `profile: <key> from legacy <path>` on stderr; a key set differently in both fails. A missing file: every key
     from its legacy home or default, and one warning.
  3. `check_spec.py --params` prints the resolver's `sdd` section, keeping the keys `spec.schema.json` defines, so its
     output is unchanged. The spec-tools action gains the `profile` input (default `.ai-kit.yaml`) and a step that
     exports `AI_KIT_PROFILE_JSON` between a random heredoc delimiter.
  4. `profile.py migrate [ROOT]` writes `.ai-kit.yaml` from the resolved view (the keys off their defaults), checks
     that the text reads back as that view, and never overwrites a file. The `sync-project.sh --migrate-profile` flag
     waits for KIT-081 stage 3, which is changing that script.
  5. Tests: `platforms/ci/validations/test_profile.py`; `test_spec_tools_action.py` gains the profile step.
  6. Docs: `docs/projects.md`, `sdd-parameters.md`, `platforms/tools/README.md`, `platforms/ci/README.md`, the action's
     README, the CHANGELOG.
- **P1b — the kit's own profile (owner, 2026-11-16, #322 "Scope addition": the kit uses the kit): done on branch
  `feat/kit-087-p1b-kit-profile`.**
  1. `.ai-kit.yaml` at the kit root sets only the keys that differ from their defaults, each commented with its
     evidence: `stacks` (`'.': docs`; `platforms/tools`, `platforms/ci` and `plugins/guardrails/hooks`: `python`) and
     `ci.trigger: auto` (`ci.yml`, `gitleaks.yml` and `codeql.yml` run on every pull request and push to `main`,
     KIT-076). `changelog.mode: file` is the default, so it is a comment, not a key; `review` and `gates` stay at their
     defaults (the kit has no gates JSON, protected-paths list or review cap of its own); `sdd` stays at its defaults
     because the kit has no `docs/spec/` and no key yet says "records in `docs/features/`" (the open point of #322,
     left for a later phase).
  2. `check_kit.py` § 15 fails when the file is missing or `profile.py resolve` exits non-zero or prints any note, so
     the static job's `check.sh --links` (required through `ci`) refuses a schema or resolver change that breaks the
     kit's own profile. Tests: `test_check_kit_readmes.py` breaks a copy (an unknown key plus a value outside the
     schema, then a missing file); `test_profile.py` `KitOwnProfile` resolves the real file with no note and checks
     that every key it sets is off its default.
  3. Protection: `.github/CODEOWNERS` already assigns every path (`*`) to the owner; the kit has no protected-paths
     list of its own, so nothing was added.
- **P2 — the kit's skills, hooks and docs read the profile**, in two parts:
  - **P2a — the tools, hooks and sync: done on branch `feat/kit-087-p2a-tools-read-profile`.**
    1. Hooks: the post-edit hook took `docs/spec/` and every `.gd` file as given; it now runs `check_spec.py` on
       `spec_root` and lints a `.gd` file only in a folder whose `stacks` include `godot` (every `.gd` file when no
       stacks are set), from the git top level. The path-rule hook selects the rules by the resolved `stacks`, the
       marker's list when the resolver gives none. Both read the profile through the new
       `plugins/guardrails/hooks/hook_profile.py`: the resolver (`$AI_KIT_DIR`, the plugin's own kit checkout, then
       `~/.ai-kit`) runs as `python3 -B -S profile.py resolve --json` with a 3 s timeout, and the view is cached per
       session in `${CLAUDE_PLUGIN_DATA}/profile/<session_id>.json`, keyed by the modification time and size of
       `.ai-kit.yaml`, `CLAUDE.md` (the legacy home of `stacks`) and the resolver; a failure is cached as no view, and
       the hook keeps its behaviour from before the profile. Both stay exit 0 on any profile error.
    2. Sync: `sync-project.sh --migrate-profile <repo>` runs `profile.py migrate` alone; a sync takes the profile list
       from the `stacks` `.ai-kit.yaml` sets (read from the file only, since the marker is what the run rewrites),
       else `--profile`, else the marker; a `--profile` that names another list, or a refused profile, exits 2 before
       any write.
    3. Duplicate keys: `review.rounds` and `evidence.visual_approval` are the homes (the sections the schema gives
       their reader phases, and where the KIT-088 `game` preset already sets `visual_approval`); `sdd.review_rounds`
       and `sdd.visual_approval` stay as legacy aliases until P4, because the legacy `sdd:` block and
       `check_spec.py --params` (row_checks.py rule j) use those names. An alias set where its home is not gives the
       home its value with a note; the two set differently fail once; the resolved alias always equals its home, kind
       preset included; `migrate` writes only the home. The pairs live in `profile.py` `ALIASES`, so
       `profile.schema.json` keeps `sdd` equal to `spec.schema.json`.
    4. Review follow-ups (#327, #344): `spec_root` matches
       `^(?!(.*/)?\.{1,2}(/|$))[A-Za-z0-9._-]+(/[A-Za-z0-9._-]+)*$` (no `./a`, `a//b` or backslash) and fails when
       it resolves outside the root through a link; a test pins `preset()` falling back to the default kind; the root
       key's note reads `stacks['.']`; `--file` must stay under ROOT (exit 2); `check_spec.py --params` prints its
       notes as one stderr line.
    5. The spec-tools action: `checks` defaults to empty, and the checks step, now after the profile step, then reads
       `ci.spec_tools_checks` from `AI_KIT_PROFILE_JSON` (default `["spec"]`, the old input default).
  - **P2b — the skill text: done on branch `feat/kit-087-p2b-skills-read-profile`.**
    1. One shared reference, `plugins/guardrails/skills/session/references/project-profile.md` (one line per skill
       instead of a block in each, so the skills stay within 80 lines): `KIT` is the first of `$AI_KIT_DIR`, the
       plugin's kit checkout and `~/.ai-kit` (the hooks' order, `hook_profile.py`); `profile.py resolve` runs once per
       skill; exit 1 stops the skill; `spec_root` replaces every `docs/spec`; § 3 names the kit tools a step runs
       (`PROFILE`, `CHECK_SPEC`, `TRACE`, `ROWS`, `RC`, `COMPLEXITY`, the GDScript tools, `AUDIT`, `SYNC`, the stack
       recipe) with their paths from `KIT`.
    2. Each skill that reads a profile key (15 of 18) resolves the profile in its first step, or in the preamble line
       that already named its parameters, and names the sections its phase reads; `parallelize`, `investigate` and
       `docker` read no key (no `x-read-by` phase is theirs) and are unchanged. Only first-step and script-call lines
       changed, in the skills and in their references; no skill body was rewritten.
    3. Docs, templates and rendered rules: `code.md` and `spec.md` say "skill `review`", "skill `sdd-implement`" and
       the editing skills where they named a kit command; the project AGENTS templates name the installed kit's recipe
       instead of the `just -f ~/.ai-kit/...` line; the `spec-index-*` frontmatter comment names skill
       `sdd-constitution`. `check_kit.py` and `test_sync_just.py` pin the recipe line as
       `just -f "$KIT/platforms/kits/just/<stack>.just" -d`.
    4. `test-gates.md` § 1 and § 2: the domain floors are `quality.<stack>` (`coverage.line`, `coverage.branch`,
       `mutation` on `domain_globs`, or `advisory`); the kit sets none (`quality` default `{}`, unchanged since
       KIT-088), per #322 decision 4. The `java-maven` kit's `domain-gate` Maven profile still enforces 100%/80%.
    5. `check_spec.load_params` (the `sdd` view `row_checks.py` and `spec_trace.py` read) resolves through
       `profile.py`: `.ai-kit.yaml` at the git top level (else `x` for `x/docs/spec`) when its `spec_root` is the
       checked folder, then the legacy `sdd:` block; the legacy reader alone without `profile.py` or its schema.
    6. KIT-095 part 2's key: `sdd.migrations` (profile only, default `[]`, rooted folders): `spec_trace.py enablers`
       walks each as `<folder>/**/*` for C19, beside `row_checks.protocol.schemas` and `--catalog`; `enablers` now
       fails on a refused `sdd` section.
- **P3 — the consumer project moves its keys to `.ai-kit.yaml`: done.** Stratics took kit 16.0.0 with its
  `.ai-kit.yaml` (dev-game-studio/stratics#4666, merged as `756b4a9`); its `sdd:` block left `spec.md`. The
  review-loop part of the first plan (the loop reads `gates` through the resolver, `gate-profile.json` folds in) is
  dropped by the owner's correction on #322 (2026-11-16): the loop keeps its own config, and each copy of a shared
  value belongs to its own reader. dev-game-studio/stratics#4674 only corrects the `.ai-kit.yaml` comment on `gates`.
- **P4 — the legacy readers go (MAJOR): implemented, release pending.**
  1. `profile.py` reads `.ai-kit.yaml` alone: no `sdd:` block of `spec.md`, no profile list of the `CLAUDE.md`
     marker, no gates JSON as a source of `gates` (so no equality check with it), no `sdd.review_rounds` or
     `sdd.visual_approval` alias (unknown keys now), no `migrate`. A missing file stays every default plus one warning.
  2. `spec.schema.json` drops `sdd`; `check_spec.py` fails (`sdd-params`) on an `sdd:` block left in `spec.md`, reads
     its task-table limits from the profile (`load_sections`), and `--params` prints the whole resolved section. A
     refused profile still fails `--params` and `profile.py`, not the spec run (KIT-100's choice, kept).
  3. `row_checks.py` rule j and `spec_trace.py governance` read `evidence.visual_approval`; `spec_trace.py validate`
     reads `sdd.release` from the resolved profile instead of `spec.md`'s frontmatter, a reader P2b missed.
     `row_checks.py` still reads the gates JSON `sdd.row_checks.gates` names for its own rules (`proof_allowlist`,
     `proof_script_runners`, `generated_neighbours`): a current key, not a legacy home.
  4. `sync-project.sh` drops `--migrate-profile` (exit 2) and the marker's list (`<!-- generated by agent-rules-kit
     sync-project.sh v<version>; AGENTS.md is the source -->`); without `stacks` it takes `--profile`, the vendored
     manifest or inference and warns. The path-rule hook accepts either marker form as its gate and selects rules by
     `stacks` only; `hook_profile.py` keys its cache on `.ai-kit.yaml` alone.
  5. The business and game `spec-index` templates carry no `sdd:` block; `sdd-constitution` § 4 writes the `sdd`
     section of `.ai-kit.yaml`; the docs, references and the eval fixtures follow.

## Proof

[FACT] P1, on this branch, macOS:

- `python3.12 -B -m unittest platforms/ci/validations/test_profile.py`: 28 tests OK; the same module and
  `test_check_spec.py` under `/usr/bin/python3` 3.9.6: `Ran 101 tests`, OK. The module covers the defaults, unknown
  keys at every level with and without pyyaml (`python -S`), each legacy fallback, the conflicts, the `x-` keys, the
  migration round trip and refusal, the `kit` pin, the 3.9 parse (`ast.parse(feature_version=(3, 9))`) and
  `--params` printing what the legacy `sdd_params` resolves on `platforms/ci/fixtures/consumer/docs/spec` and on the
  `spec-index.md` template.
- `run_tests.py --layer unit,contract`: `Ran 221 tests`, `OK (skipped=16)` (gdtoolkit);
  `run_tests.py --layer integration --changed-from origin/main`: `Ran 326 tests`, `OK (skipped=1)` (a non-UTF-8 file
  name this file system refuses).
- `check.sh` with `python3` at 3.12: `check: OK (1 plugins, 18 skills, 11 rules, 13 templates, 15 readmes, 156 links,
  57 hook cases, 18 shell scripts)`, `plugin indexes are current`; `zizmor --offline` 1.32.0 on the action: no
  findings; ShellCheck and `/bin/bash -n` on the new step: clean.
- Not run here: the action on a GitHub runner, the functional layer, the evals for the edited reference
  `sdd-parameters.md`, and the resolver on a real consumer checkout.

[FACT] P1b, on its branch, macOS:

- `platforms/tools/check.sh` (system `python3` 3.9.6) and `check.sh --links` with `python3` at 3.12: `check: OK (1
  plugins, 18 skills, 11 rules, 13 templates, 15 readmes, 159 links, 63 hook cases, 18 shell scripts)`; `profile.py
  resolve` on the kit exits 0 under 3.12 and under `/usr/bin/python3 -S` 3.9.6 (fallback parser).
- `run_tests.py --layer unit,contract`: `Ran 258 tests`, `OK (skipped=16)` (gdtoolkit);
  `run_tests.py --layer integration --changed-from origin/main`: `Ran 71 tests`, OK;
  `test_profile.py` under `/usr/bin/python3` 3.9.6: `Ran 29 tests`, OK.
- Not run here: the static job on a GitHub runner.

[FACT] P2a, on its branch, macOS:

- Red first, then green: `test_profile.py` `P2aFollowUps` and `DuplicateKeys` and three command-line tests (`--file`,
  the `--params` summary, `migrate` writing only the home); `test_hooks_profile.py` (new: the helper, the post-edit
  hook through bash with stub tools, the path-rule hook with the real resolver); `test_sync_project.py` (the profile's
  stacks, a differing `--profile`, a refused profile, `--migrate-profile`); `test_spec_tools_action.py` (checks from
  the profile). Pins that passed before the change: `preset()` falling back, equal alias values, a profile without
  `stacks`, the hook without a view.
- Hook latency, system `/usr/bin/python3` 3.9.6, 10 sessions each, medians: the post-edit hook on `README.md` 53 ms
  before, 130 ms on a session's first call (one resolver run), 58 ms cached; the path-rule hook 45 ms before, 55 ms
  cached; `test_hooks_profile.py` `Latency` (Python 3.12): uncached view 94-98 ms, cached 0.1 ms.

[FACT] P2b, on its branch, macOS:

- Red first, then green: the new tests, run against an `origin/main` export with the code of `7800238`, failed 36
  times (`test_profile.py` `LoadParams`, `SkillsReadTheProfile` and the `sdd` key contract;
  `test_spec_trace_enabler.py` `MigrationsFromProfileTest`), and pass on the branch. Pins moved to the `"$KIT"` form
  with the same strictness: `test_sync_just.py` `SkillNamesTheCommand`, `test_sync_project.py` (every kit path a skill
  names exists; the rendered code rule names skill `review`), and `test_check_kit_readmes.py` (new: the fixed
  `~/.ai-kit` recipe line alone fails `check_kit.py`).
- `check.sh` and `check.sh --links`: `check: OK (1 plugins, 18 skills, 11 rules, 16 templates, 15 readmes, 169 links,
  65 hook cases, 18 shell scripts)`; `run_tests.py --layer unit,contract`: `Ran 310 tests`, `OK (skipped=16)`
  (gdtoolkit); `--layer integration --changed-from origin/main`: `Ran 615 tests`, `OK (skipped=1)`; the touched test
  modules under `/usr/bin/python3` 3.9.6: `Ran 352 tests`, `OK (skipped=2)`.
- Not run here: `claude plugin eval` for the edited skills, CI on a runner, and the skills on a real consumer.

[FACT] P4, on its branch, macOS:

- Red first, then green: the branch's tests, run against an `origin/main` export with main's code, failed 15 times in
  13 tests (`test_profile.py` `LegacyHomesAreNotRead`, `OneHomePerSetting`, the `check_spec.py` `sdd:` block test,
  `migrate` gone from the usage line, the `sdd` schema contract; `test_hooks_path_rules.py` the old marker's list;
  `test_sync_project.py` `--migrate-profile` and the profile-stacks-only list; `test_spec_trace_versions.py`
  `test_deliver_moves_the_block`, `release` from the profile), and pass on the branch.
- `check.sh`: `check: OK (1 plugins, 18 skills, 11 rules, 18 templates, 15 readmes, 178 links, 65 hook cases, 18 shell
  scripts)`; `run_tests.py --layer unit,contract`: `Ran 308 tests`, `OK (skipped=16)` (gdtoolkit); `--layer
  integration --changed-from origin/main`: `Ran 1099 tests`, `OK (skipped=43)`; `test_profile.py`,
  `test_check_spec.py` and `test_hooks_profile.py` under `/usr/bin/python3` 3.9.6: `Ran 154 tests`, `OK`.
- Stratics at `756b4a9` (a read-only `git archive` export): `profile.py resolve` exits 0 with no stderr under 3.12 and
  3.9, with and without `-S`; the resolved view equals kit 16.0.0's but for the two dropped alias mirrors;
  `check_spec.py`, `row_checks.py check --all` and `spec_trace.py check` print byte-identical output on this branch and
  on `~/.ai-kit` 16.0.0.
- Not run here: the functional layer and `smoke.sh`, `claude plugin eval` for the edited skills and eval fixtures, CI
  on a runner.

## What would prove it wrong

- A consumer still on a legacy home when it takes the P4 release resolves those keys at their defaults with no note
  (only a leftover `sdd:` block fails, in `check_spec.py`); the Migration note asks for the move with kit 16 first.
- A YAML form a project needs that the fallback parser does not read (a multi-line string, an anchor) would make the
  profile unreadable on a machine without pyyaml.

## History

- 2026-11-16: confirmed (owner, "sim abre a 087", then "concordo com as 6"); P1 started in parallel with KIT-081 stage 3.
- 2026-11-16: owner scope correction: the profile holds only parameters the kit reads; `gates` keeps the kit-read
  keys and `tracker.labels` the labels the kit's tooling uses.
- 2026-11-16: P1 implemented on `feat/kit-087-p1-profile-resolver`.
- 2026-11-16: owner scope addition (#322): the kit carries its own profile; P1b implemented on
  `feat/kit-087-p1b-kit-profile`.
- 2026-11-16: P2 split into P2a (tools, hooks, sync) and P2b (skill text); P2a implemented on
  `feat/kit-087-p2a-tools-read-profile`.
- 2026-11-17: P2b implemented on `feat/kit-087-p2b-skills-read-profile`, with the `sdd.migrations` key KIT-095 part 2
  needs.
- 2026-11-17: P3 closed (Stratics on kit 16 with `.ai-kit.yaml`, `756b4a9`; the review-loop part dropped by the
  owner's 2026-11-16 correction); P4 implemented on `claude/kit-087-p4-drop-legacy-1a80eb`.
