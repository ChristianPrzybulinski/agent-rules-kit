---
id: KIT-083
title: "Fix the small findings of the KIT-081 reviews"
status: in-progress
confirmed: "2026-11-16 (owner, chat of the kit session: \"Sua recomendação, quem sabe paralelizar?\", on running these fixes beside the KIT-081 stage 3 measurement)"
issue: "#317"
pr: ""
---

# KIT-083 — Fix the small findings of the KIT-081 reviews

The independent reviews of the KIT-081 pull requests (#309, #310, #313, #314) and the test review of 2026-11-16 left
seven small findings that need no design decision. Each was confirmed on `origin/main` `ee41169` (release 14.0.0 plus
#316) before its fix, and each fix has a test that failed there. None was dropped.

## Problem and evidence

[FACT] Read and reproduced on `ee41169`, macOS, Python 3.12; the Red line is the new test's failure on that code:

1. **Nothing to vendor.** `platforms/kits/third-party/skills.lock` holds its header line and no entry (KIT-070 removed
   `grilling`, the last vendored skill), yet `platforms/tools/vendor.sh`, the lock, its README,
   `platforms/ci/schemas/skills-lock.schema.json`, `check_kit.py` § 11 (`check_kit.py:1333`), the CONTRIBUTING
   section `## Third-party skills` and rows of three READMEs still described the vendoring. Red:
   `test_check_kit_readmes.NoVendoringToolTest`: `True is not false : platforms/tools/vendor.sh`.
2. **A settings file rewritten with nothing removed.** `sync_unvendor.py remove` re-serialized `.claude/settings.json`
   whenever the text differed from its own `indent=2` output (`sync_unvendor.py:193`), whether or not it took a key or
   hook out. Through `sync-project.sh`, which writes that file in the same format first, the file never changed; run on
   its own, a repository whose only leftover is a skill copy had its settings reformatted. Red:
   `test_sync_project.UnvendorSettingsTest.test_settings_without_kit_state_are_not_rewritten`: the compact file came
   back as `{\n  "enabledPlugins": ...`.
3. **A comment or a trigger reported as a caller.** `sync_spec_tools.py` skipped only whole comment lines
   (`code_lines`, line 98) and matched `.github/spec-lint/` anywhere in the rest (`copy_callers`, line 114), so
   `sync-project.sh --check` failed on a trailing comment and told a `paths:` filter entry to "run the spec tools
   through the spec-tools action". Red: `test_sync_spec_tools.SpecTools.
   test_a_trailing_comment_names_nothing_and_a_paths_entry_is_a_stale_trigger`: the six-line list held the three
   trailing comments and the caller's fix text instead of three stale-trigger lines.
4. **A silent baseline step.** The spec-tools action's `Baseline only shrinks` step (`action.yml:78`) ran its check
   only when the base input was set and its commit held `docs/spec/baseline.json` (`action.yml:84`), and printed
   nothing otherwise, also when the base commit was missing from a shallow checkout. Red:
   `test_spec_tools_action.SpecToolsActionRuns.test_the_baseline_step_says_why_it_compares_nothing`: `'' != '::notice::
   spec-tools: no base commit ...'` for each of the three cases.
5. **Another kit served the `just` imports with a warning only.** The link step (`action.yml:61` to `66`) left an
   existing `~/.ai-kit` in place with a `::warning::` whatever its commit, so a project's justfile imported that kit,
   not the pinned one. Red: `test_it_links_home_ai_kit_to_its_own_commit_unless_a_kit_is_there`: `0 != 1` with the old
   warning, and `test_a_kit_already_at_home_passes_only_at_the_actions_commit`: the warning instead of the notice.
6. **Map lines without a reader.** The 18 `skills/` lines of `platforms/tools/sync-profiles.txt` (lines 18 to 35) chose
   the vendored copies KIT-081 stage 2b removed; `sync-project.sh` reads only the `rules` lines (`map_selected rules`,
   `map_entries rules` at lines 143, 283 and 461), and `check_kit.py:1375` still required a line per skill. Red:
   `test_check_kit_readmes.CheckKitReadmesTest.test_each_violation_is_reported`: no `'skills/session' is not a rule`
   line.
7. **One switch in three copies.** KIT-082's `CI=1` gdtoolkit switch `NEEDS_PARSER` was written into
   `test_gd_coverage.py:29`, `test_gd_duplicates.py:19` and `test_gd_mutation.py:27`, and only the last handled a
   class. Red: `test_needs_parser`: `ModuleNotFoundError: No module named 'needs_parser'`.

## Change

1. **Removed** `platforms/tools/vendor.sh`, `platforms/kits/third-party/` (`skills.lock` and its README, so the folder
   goes), `platforms/ci/schemas/skills-lock.schema.json` and `check_kit.py` § 11; the CONTRIBUTING section, the README
   license line, and the rows of `platforms/tools/README.md`, `platforms/kits/README.md` and `platforms/ci/README.md`
   follow. `NoVendoringToolTest` (contract layer) keeps the three paths absent and their names out of every file but
   the CHANGELOG and the KIT records. Not removed: `check_kit.py`'s exemptions for a skill folder with a `VENDOR.md`,
   which name no removed file and which a later change may drop.
2. `sync_unvendor.py remove` writes `.claude/settings.json` only when it removed the pinned key or a pinned hook.
3. `sync_spec_tools.py` cuts a trailing comment (a `#` at the start or after a space or tab, outside quotes) before it
   matches, and names an entry of a `paths` or `paths-ignore` filter under the top-level `on:` key as what it is:
   `<file>:<line> names .github/spec-lint/ in a paths filter, a stale trigger: the kit no longer writes that folder;
   remove the entry`. Such a line still fails `--check` and warns on install; a line that runs the old copy keeps its
   message.
4. The baseline step prints a `::notice::` without a base input, a `::warning::` when the base commit is not in the
   checkout (`fetch-depth: 0` fetches it), and a `::notice::` when the base commit has no baseline.
5. The link step compares an existing `~/.ai-kit`'s `HEAD` with the action's commit: the `HEAD` of the action's
   checkout when it is a git checkout, else the SHA the caller pins (`github.action_ref`, passed through `env:`), since
   a runner downloads an action as an archive without `.git`. The same commit passes with a `::notice::`; another
   commit, no git checkout at `~/.ai-kit` or an unknown action commit (a pin by tag) fails with an `::error::` that
   names both commits and the fix. A `~/.ai-kit` that already resolves to the action's checkout passes silently, as
   before.
6. `sync-profiles.txt` keeps the 11 rule lines; `check_kit.py` § 11b requires one line per rule and fails on any other
   entry (`'<entry>' is not a rule of plugins/guardrails`). `sync-project.sh` is unchanged.
7. `platforms/ci/validations/needs_parser.py` holds `HAS_GDTOOLKIT` and `NEEDS_PARSER` (the class-aware version); the
   three modules import it and list it in `COVERS`, and `test_needs_parser.py` (unit layer) tests its three outcomes on
   a method and on a class.

## Proof

[FACT] On this branch, macOS, Python 3.12, load average about 25 (other sessions running):

- The Red runs above, then the same tests green after each fix.
- `run_tests.py --layer unit,contract`: `Ran 173 tests`, `OK (skipped=16)` (the gdtoolkit unit tests).
- `run_tests.py` on the 18 modules that cover the changed files (`test_check_kit_readmes`, `_skill_use`,
  `_references`, `test_hooks_context`, `test_just_modules`, `test_bump_version`, `test_sync_project`,
  `test_sync_dev_standards`, `test_sync_spec_tools`, `test_spec_tools_action`, `test_check_spec`, `_tasks`,
  `_closure`, the three `test_gd_*`, `test_needs_parser`, `test_run_tests`): `Ran 363 tests`, `OK (skipped=59)` (54
  gdtoolkit, 4 Godot, 1 non-UTF-8 file name).
- `check.sh` with `python3` at 3.12: `check: OK (1 plugins, 18 skills, 11 rules, 13 templates, 14 readmes,
  155 links, 57 hook cases, 18 shell scripts)`, `plugin indexes are current`, both `claude plugin validate` passed;
  `smoke.sh`: `smoke: OK (18 skills, ...)` in 115 s.
- The three `test_gd_*` modules without gdtoolkit: 58 skips (54 gdtoolkit, 4 Godot), as before; `test_gd_duplicates`
  with `CI=1` and no gdtoolkit: `FAILED (failures=7)`, as KIT-082 recorded.
- `zizmor --offline` 1.32.0 on the action: no findings (the one suppressed finding is the base's); ShellCheck and
  `/bin/bash -n` (3.2) on each `run:` step of the action: clean.
- Not run here: the whole integration and functional layers (CI's jobs), the GDScript tool tests with gdtoolkit
  installed (CI installs it), zizmor's online audits, and the action on a GitHub runner.

## What would prove it wrong

A self-hosted runner whose `~/.ai-kit` sits at the commit the caller pins and where `github.action_ref` reaches the
step empty: the link step then fails with "this action's commit is unknown" although the kits match. The step was
tested with a local git checkout and a copy without `.git`, never on a GitHub runner.

## History

- 2026-11-16: confirmed (owner, "Sua recomendação, quem sabe paralelizar?").
