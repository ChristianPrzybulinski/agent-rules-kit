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
  - **P2b — the skill text: open.** Each skill's first step resolves the profile; the kit's direct script calls in
    skills take their paths from the resolver and those in docs, templates and the rendered rules become "skill X";
    the `test-gates.md` coverage policy becomes `quality` values a project sets; `load_params` (row_checks.py,
    spec_trace.py) reads the profile.
- **P3 — the consumer project moves its keys to `.ai-kit.yaml`: open.** Its `sdd:` block and marker stack list go,
  and its direct calls become "skill X".
- **P4 — the legacy readers go (MAJOR): open.** In the first release after P3 runs clean.

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

## What would prove it wrong

- A consumer's gates JSON whose `repos` entries or `protected_paths` do not fit the `gates` schema would fail the dual
  read until the file is fixed; only the keys kit tools read are taken from it.
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
