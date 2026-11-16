---
id: KIT-077
title: "Layered gate: a fast PR gate, a full gate on main and release, and a review bar by risk"
status: confirmed
confirmed: "2026-11-15 (owner, chat of the coordinator session \"Revisão de regras e skills\": \"Sim, aplique\")"
issue: "#281"
pr: "#286 (items 5–6), #293 (items 1–4)"
---

# KIT-077 — Layered gate: a fast PR gate, a full gate on main and release, and a review bar by risk

Status: items 5 and 6 are done (#286, in 13.0.0); items 1–4 are delivered by #293. The record stays `confirmed`
until its Done when holds on `main`: `ci-full` green there and the median pull request `ci` time measured.

## Problem and evidence

[FACT] From #281, measured on the 13.0.0 pull requests:
- The required `ci` job took 5m51s on #272 (548 tests) and 14m06s on #261 (560 tests).
- A local full run took `Ran 674 tests in 632.920s` (#262 review).
- Review rounds: #261 three, #262 three, #260 two, each 10–35 min. #262's rounds chased bash spellings in a hygiene
  check (#280).
- The whole suite ran three times per PR: the author ran it, the reviewer ran it again, and CI ran it a third time.

## Change

The owner's test standard (2026-11-15): each test layer has one place and one trigger, CI is the gate, and a review is
one round that reads the diff against the FEAT plus the CI result. Six items; items 5 and 6 change what consumers read,
so they go into 13.0.0, and items 1–4 (the CI layering) may land after it.

1. Tag each test with its layer. *After 13.0.0.*
2. The required `ci` runs the PR layers in parallel, 3 min or less. *After 13.0.0.*
3. `ci-full` on push to `main`, nightly and on the release commit; `release.yml` refuses a tag without it.
   *After 13.0.0.*
4. Logic-only sync tests become in-process unit tests; the hook timing test moves to the performance layer (#278
   folds in). *After 13.0.0.*
5. **The review bar** (delivered):
   - skill `review`, its § 1 steps, § 2 and § 4: one round per PR; the reviewer reads the diff against the criteria
     plus the required gates' result recorded for the exact head (the CI checks, or the project's gate record where it
     runs no CI on pull requests, so a consumer without PR CI keeps its gate). Only when no such result exists for
     that head does it run the gates and the cited proofs, once, on a clean checkout; beyond that it runs nothing,
     except a targeted probe at a security boundary;
   - a finding blocks only for (a) an unmet acceptance criterion, (b) broken existing behavior (a failing test, a
     reproduced regression, or a weakened check the PR does not name), (c) a security gap where untrusted input
     enters, or (d) a rule lost in a migration. Everything else goes to one follow-up issue;
   - a small fix delta with no new mechanism is verified by the coordinator (red check plus a targeted probe), with no
     new round;
   - its reference `delivery-steps.md`: recorded results first, the clean checkout as the fallback, the security
     probe, and a verdict that lists gate sources, blocker reasons and the follow-up issue; agent `reviewer`
     (`plugins/guardrails/agents/reviewer.md`) follows the same rule (coordinator widening, 2026-11-16);
   - the `platforms/kits/github/REVIEW.md` template: § The review bar replaces § Important means, and § Scope checks
     the `Evals:` line.
6. **Local runs** (delivered):
   - skill `sdd-implement` § 2 and its references `test-gates.md` § 3 and `task-pr.md`: implementers run locally only
     the TDD loop (the unit and integration tests covering the changed files) and the linters, and CI runs the rest.
     Where a repository runs no CI on each push, its gate command or loop gate stands in;
   - a PR that changes skills or rules runs their evals by hand before it opens and cites the command and the score
     on an `Evals:` line;
   - `.github/CONTRIBUTING.md` and `.github/PULL_REQUEST_TEMPLATE.md` say the same for this repository.
     `evals.yml` stays dispatch-only, with no Anthropic secret.

## Items 1–4: the layered CI (#293)

### Measured before (`0784b81`)

[FACT] One serial run of the whole suite at `0784b81` with a per-test timing runner, on macOS with Python 3.12, `CI=1`
and CI's tools (no `just`, `gitleaks`, Godot or gdtoolkit on `PATH`), load average 5–7: 870 tests in 779.8 s, 87
skipped, no failure. The 20 slowest tests, then the time per module:

| # | Seconds | Test |
|---|---|---|
| 1 | 34.1 | `test_hooks_instructions_loaded.CheckKitInstructionsLoadedTest.test_check_kit_fails_a_broken_hook` |
| 2 | 22.1 | `test_check_kit_readmes.CheckKitReadmesTest.test_a_link_out_of_the_plugin_and_a_missing_not_for_fail` |
| 3 | 21.7 | `test_bump_version.BumpVersionTest.test_bump_keeps_check_kit_green` |
| 4 | 20.6 | `test_check_kit_readmes.CheckKitReadmesTest.test_an_odd_apostrophe_in_a_heredoc_inside_command_substitution_fails_under_bash_3` |
| 5 | 20.3 | `test_check_kit_readmes.CheckKitReadmesTest.test_each_violation_is_reported` |
| 6 | 20.2 | `test_check_kit_references.CheckKitNestedReferencesTest.test_a_deeper_path_is_no_listing_of_a_sibling` |
| 7 | 19.7 | `test_check_kit_readmes.CheckKitReadmesTest.test_a_shell_script_bash_cannot_parse_fails` |
| 8 | 19.7 | `test_check_kit_readmes.CheckKitReadmesTest.test_the_copy_passes_and_a_folder_needs_no_readme` |
| 9 | 16.8 | `test_check_kit_references.CheckKitNestedReferencesTest.test_index_name_matches_whole_path_components` |
| 10 | 15.6 | `test_check_kit_references.CheckKitNestedReferencesTest.test_deeper_index_is_named_in_its_parent_index` |
| 11 | 15.5 | `test_check_kit_skill_use.CheckKitSkillUseTest.test_the_copy_passes` |
| 12 | 14.9 | `test_check_kit_skill_use.CheckKitSkillUseTest.test_drifted_append_fails` |
| 13 | 14.9 | `test_check_kit_references.CheckKitNestedReferencesTest.test_nested_reference_keeps_the_line_limit` |
| 14 | 14.3 | `test_check_kit_references.CheckKitNestedReferencesTest.test_deeper_folders_get_every_check` |
| 15 | 13.8 | `test_check_kit_references.CheckKitNestedReferencesTest.test_nested_index_is_named_in_the_skill` |
| 16 | 13.7 | `test_check_kit_references.CheckKitNestedReferencesTest.test_nested_reference_is_listed_in_its_index` |
| 17 | 13.5 | `test_check_kit_references.CheckKitNestedReferencesTest.test_nested_folder_needs_a_readme_index` |
| 18 | 12.3 | `test_just_modules.TemplatesNameKitRecipes.test_an_agents_template_naming_a_missing_recipe_fails` |
| 19 | 12.1 | `test_hooks_context.CheckKitCatchesBrokenHooksTest.test_ignored_custom_attribution_fails` |
| 20 | 12.0 | `test_check_kit_skill_use.CheckKitSkillUseTest.test_user_only_preload_fails` |

| Module | Tests | Seconds |
|---|---|---|
| `test_check_kit_references` | 10 | 145.2 |
| `test_sync_project` | 72 | 144.2 |
| `test_check_kit_readmes` | 5 | 102.4 |
| `test_check_kit_skill_use` | 6 | 76.0 |
| `test_hooks_context` | 17 | 58.5 |
| `test_review_checks` | 101 | 48.0 |
| `test_just_modules` | 25 | 45.5 |
| `test_hooks_instructions_loaded` | 8 | 34.4 |
| `test_sync_dev_standards` | 23 | 31.0 |
| `test_bump_version` | 5 | 26.6 |
| `test_session_audit` | 24 | 14.9 |
| `test_check_spec` | 72 | 8.7 |
| `test_hooks_guard_merged_branch` | 9 | 8.5 |
| `test_check_spec_tasks` | 37 | 4.8 |
| `test_hooks_guard_compact` | 10 | 4.2 |
| `test_sync_project_spec_tools` | 5 | 4.1 |
| `test_check_docs_structure` | 22 | 3.9 |
| `test_complexity` | 12 | 3.3 |
| `test_spec_trace` | 51 | 1.9 |
| `test_check_spec_closure` | 14 | 1.6 |
| `test_row_checks` | 47 | 1.3 |
| `test_keyed_csv_merge` | 26 | 1.3 |
| `test_spec_trace_sync_status` | 34 | 1.1 |
| `test_row_checks_contract` | 26 | 0.9 |
| `test_spec_trace_checklist` | 22 | 0.9 |
| `test_gd_duplicates` | 9 | 0.7 |
| `test_gd_mutation` | 45 | 0.7 |
| `test_gen_index` | 9 | 0.5 |
| `test_gd_coverage` | 23 | 0.4 |
| `test_spec_trace_closure` | 17 | 0.3 |
| `test_spec_trace_lint` | 22 | 0.3 |
| `test_kpi` | 5 | 0.3 |
| `test_kit_workflows` | 17 | 0.1 |
| `test_skill_usage` | 12 | 0.0 |
| `test_pr_gates_inputs` | 5 | 0.0 |
| `test_gitleaks_template` | 5 | 0.0 |
| `test_pr_gates_command` | 18 | 0.0 |

Most of the time goes to the tests that copy the kit and run `check_kit.py` on the copy (10–34 s each) and to the sync
tests (72 tests in `test_sync_project`, about 2 s each, one `sync-project.sh` run or more per test).

[FACT] The 87 skips in CI (87 at #263's head `f3472a9`, 87 in the run above, which swaps one macOS-only skip for one
Linux-only skip):

| Skipped | Tests | Why |
|---|---|---|
| gdtoolkit not installed | 54 | `test_gd_coverage` (15), `test_gd_duplicates` (7), `test_gd_mutation` (32) |
| Godot, gdtoolkit and `KIT_GDUNIT4` | 4 | `test_gd_coverage.GodotTest` |
| `just` not on `PATH` | 21 | `test_just_modules` (`RecipeNames`, `Godot`, `Java`, `Python`, `Docs`) |
| `gitleaks` not on `PATH` | 6 | `test_gitleaks_template.Scan` (3), `test_kit_workflows.GitleaksRange` (3) |
| `SPEC_TRACE_CORPUS` unset | 1 | `test_spec_trace.CorpusTest`, opt-in on a real spec folder |
| bash is not 3.2 | 1 | `test_check_kit_readmes`: the bash 3 parse trap runs only on macOS (CI's bash is 5) |

The local run skips the non-UTF-8 file name test of `test_sync_project` instead (macOS refuses such a name), and runs
the bash 3 test. [FACT] The required `ci` job took a median of 771 s over the last five pull request runs
(`4ea3a7a` 986 s, `8cbf7f4` 771 s, `4bc54e6` 1129 s, `49a766f` 769 s, `07c03db` 713 s), and 1120 s on the push of
`0784b81`: one serial job of setup, `check.sh`, the whole suite (11–16 min), `smoke.sh` and the links check.

### Delivered

1. **Layers.** Every test module sets `LAYER`; a class, or one test method (`test_x.LAYER = "performance"`), may set its
   own. An integration class lists in `COVERS` the globs of the files it exercises. The classification comes from a
   probe that counted the processes each test class starts: a class that starts none is `unit` (or `contract` when it
   reads the kit's own workflow files), any other is `integration`. After this change: 919 tests, of them 119 unit, 27 contract,
   766 integration, 4 functional and 3 performance.
   `platforms/tools/run_tests.py` selects by layer and runs the tests in parallel worker processes (a unit or contract
   class per chunk, any slower test alone), keeps unittest's report lines and lists the skips by reason;
   `check.sh --tests` calls it, so CI and a local run share the entry (#278).
2. **The pull request gate.** `ci.yml` runs `static`, `unit` (unit and contract), `integration (1)` to `(3)` (the
   integration classes the change reaches, `--changed-from HEAD^1`) and `red` in parallel; the required `ci` job needs
   all of them, runs `if: always()` and passes only when each passed. `red` (`platforms/tools/ci_red.py`) records
   `review_checks.py red` on the merge commit in its job summary; OK, EXEMPT, FLAG and a NONE whose `## Red` names an
   exception pass, so only a real FAIL fails `ci` (#281: the red check is required on every pull request). The
   required names `ci` and `workflow-lint` are unchanged.
3. **The full gate.** `ci-full.yml` runs the whole integration layer (three shards) and the functional layer (the
   consumer project in `platforms/ci/fixtures/consumer/` synced in plugins and vendored mode, then its spec lint,
   `just verify` in both profile folders, `sync-project.sh --check` and an idempotent resync; and the whole `smoke.sh`)
   on every push to `main`, nightly and on demand. `performance.yml` runs the latency budgets nightly and on demand,
   one test at a time. `release.yml` runs `platforms/tools/release_guard.py` first: it waits up to 20 min while the
   tagged commit's `ci-full` run is not created, queued or in progress, and fails on a completed run that is not green
   or on the timeout, so no release is published. It never deletes or moves the tag, which the ruleset
   `protect-release-tags` forbids: the release follows by re-running `release.yml` once `ci-full` is green on that
   commit, or with the next patch version. The jobs that run the `just` and `gitleaks` tests install both, pinned by
   sha-256, and under `CI=1` a missing tool fails those tests instead of skipping them (#283 item 1).
4. **Logic-only sync tests in-process, the timing tests out of the suite.** The map below. `smoke.sh --main` stops after
   its main path (bootstrap into an empty home, the Codex `AGENTS.md` link and its repoints, a clean doctor run), which
   `test_smoke.py` runs as one integration test; the whole script is a functional test.

### Test map (old → new)

Every other test keeps its name and body; it only gained its layer. Nothing is skipped, loosened or given a longer
timeout.

| Old | New | What still covers the wiring |
|---|---|---|
| `test_sync_project` `test_agents_md_keeps_the_dominant_line_ending` | `test_sync_agents_md` `LineEndings.test_write_keeps_the_dominant_lf_ending` (unit) | `test_agents_md_block_per_folder` |
| `test_sync_project` `test_agents_md_keeps_crlf_line_endings` | `LineEndings.test_write_keeps_crlf_and_a_second_run_changes_nothing` (unit) | same |
| `test_sync_project` `test_agents_md_block_removal_keeps_the_blank_line` | `Removal.test_removing_the_block_keeps_the_blank_line` (unit) | `test_agents_md_block_follows_rule_paths` |
| `test_sync_project` `test_agents_md_refuses_broken_markers` | `Refusals.test_broken_markers_refuse_every_mode_and_change_nothing` (unit) | `test_agents_md_refuses_a_folder_outside_the_repo`: the refusal precedes the sync's first write |
| `test_sync_project` `test_agents_md_refuses_a_symlinked_agents_md` | `Refusals.test_a_symlinked_agents_md_is_refused` (unit) | same |
| `test_sync_project` `test_agents_md_refuses_a_folder_reached_through_a_symlink` | `Refusals.test_a_folder_reached_through_a_symlink_is_refused` (unit) | same |
| `test_sync_project` `test_agents_md_skips_a_nested_checkout` | `Scope.test_a_nested_checkout_keeps_its_own_block` (unit) | `test_check_flags_agents_md_drift` |
| `test_sync_project` `test_agents_md_skips_a_missing_folder` | `Scope.test_a_missing_folder_gets_no_block` (unit) | same |
| `test_sync_project` `test_rule_paths_into_a_skipped_folder_warns` | `Scope.test_a_folder_the_scan_skips_warns_and_still_gets_its_block` (unit) | `test_rule_paths_for_a_rule_outside_the_profile_warns` (the sync passes the helper's warnings on) |
| `test_sync_dev_standards` `JustModules.test_a_project_justfile_is_kept_and_must_import_kit_just` | `test_sync_just` `ProjectJustfile.test_a_project_justfile_is_kept_and_must_import_kit_just` (unit) | `JustModules.test_a_root_profile_gets_kit_just_and_a_starter_justfile` |
| `test_sync_dev_standards` `JustModules.test_check_flags_an_edited_module` | `Modules.test_check_flags_an_edited_module` (unit) | same |
| `test_sync_dev_standards` `JustModules.test_a_dropped_profile_takes_its_module_and_keeps_the_justfile` | `Modules.test_a_dropped_profile_takes_its_module_and_keeps_the_justfile` (unit) | `JustModules.test_monorepo_folders_get_their_own_module` |
| `test_sync_dev_standards` `JustModules.test_a_missing_folder_is_named` | `Modules.test_a_missing_folder_is_named` (unit) | same |
| `test_hooks_guard_compact` `HooksTest.test_each_hook_within_budget` | same test, layer `performance` | `performance.yml` |
| `test_hooks_context` `ContextHooksTest.test_latency_budget` | same test, layer `performance` | `performance.yml` |
| `test_hooks_instructions_loaded` `InstructionsLoadedHookTest.test_stays_within_budget` | same test, layer `performance` | `performance.yml` |
| `ci.yml` step `smoke` (the whole `smoke.sh` on every pull request) | `test_smoke` `SmokeMainPath` (integration, `smoke.sh --main`) and `SmokeWhole` (functional) | `ci-full.yml` |

A mutation of each helper the converted tests cover (the dominant line ending, the nested-checkout skip, the module
divergence, the stale-module removal) fails them. `test_hooks_guard_compact`'s guard time on contrived input (1 s, the
KIT-054 backtracking guard) stays in the integration layer: it is a regression guard, not a latency budget.

### Measured after

The pull request run at `985b9ce`, the worst case (it changes `run_tests.py` and every test module, so the shards ran
the whole integration layer and `red` ran every module on base and head):

- From the first job's start to the `ci` job's end: 2 min 14 s (06:20:21–06:22:35), against the 771 s median before.
  Jobs: `static` 42 s, `unit` 10 s, `integration (1)` 2 min 07 s, `(2)` 1 min 26 s, `(3)` 1 min 50 s.
- `red` took 5 min 49 s and was not yet in `ci`'s needs. The review of #293 put it there, so on this worst case `ci`
  ends with `red`, at about 6 min; a pull request that changes few test modules runs a shorter `red`.
- Skips: 59, down from 87. They are 54 gdtoolkit, 4 Godot and 1 bash 3.2. The 21 `just` and 6 `gitleaks` skips are
  gone, and the corpus test is functional, so it no longer runs in a pull request job.

Pending: the median over five pull request runs, which needs runs of smaller changes.

## Proof

`python3 platforms/ci/validations/check_kit.py --links` (line limits, reference schema, links) and the tests that
cover the changed files; results in the PR. The evals run once before the 13.0.0 tag (coordinator).

## What would prove it wrong

A regression that reaches a consumer project and that the old full PR suite would have caught. Count these per
release in History.

## History

- 2026-11-15: confirmed (owner, through the coordinator session); issue #281.
- 2026-11-16: items 5 and 6 delivered for 13.0.0; items 1–4 follow the release.
- 2026-11-16: items 1–4 delivered (#293): the layers, the parallel pull request gate, `ci-full`, the release
  guard and the converted sync tests; #278 folds in.
