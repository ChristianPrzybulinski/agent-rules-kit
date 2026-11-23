---
id: KIT-069
title: "The delivery side of the SDD flow: implement modes and task cycle, review steps backed by scripts, sdd-review closes a FEAT, sdd-release delivers it"
status: done
confirmed: "2026-11-14 (owner, chat of the SDD review session: \"concordo\" for the acceptance, review and release design; \"Aprovo todos\" for the six further adjustments; \"orquestre a implementação de tudo que passamos\" and \"Já libero todos os merges. Faça tudo com autonomia pra entregar\" for this run)"
issue: "#242"
pr: "#246"
---

# KIT-069 — Delivery side: implement, review, sdd-review, sdd-release

## Problem and evidence

[FACT] At `540b6d5` (KIT-067's head) the chain ends at `implement → review`. `sdd-implement` takes "one task issue",
orients on `docs/spec/progress/FEAT-nnn.json` and asks for no Red evidence; `review` § 1–§ 4 runs every check as model
reading; nothing runs a FEAT's criteria on `main` after its last row; no step sets a NEED `delivered`
(`spec_trace.py` `delivered_by_its_feats`: "no step owns that move yet"); and `spec_trace.py status` derives
`delivered` from task rows alone ("all done → delivered"), so a FEAT is delivered without a closure, a release or an
acceptance.

[FACT] In a consumer project the review child is the loop's costliest line: about US$ 334 over 572 rounds against
about US$ 83 for Devin implement (ledger to 2026-11-10, the owner's design notes of 2026-11-14, adjustment 4).

[FACT] The owner's analysis of 2026-11-14 (`ANALYSIS-KIT-DELTAS-2026-11-14.md` § 2) found the consumer's loop prompts
restate or contradict the kit on delivery: the reviewer fixes and pushes docs PRs (P1), light review skips the FEAT row
and defers style to a batch review with no prompt (P5), rows are marked done with no progress file (P6), the child never
commits and a Claude round runs no proof (P7), and head caps are prose (P8). Its KIT-NEW items add blocked-child
handling, conflict merges that keep both sides with a net-diff check, batch review, planned versus measured evidence, a
coordinator per delivery with blocker classes A/B/C, and the fold of settled decisions at closure (ARCHITECT.md delta 9),
whose row-derived `delivered` contradicts the approved statuses.

[FACT] On the consumer's `docs/spec` at stratics-docs `8549f51d4` (an export, read only): 83 FEATs are `delivered`,
22 `in-progress`, 23 `proposed` and 1 `cancelled`; task rows are `done` 1,370, `todo` 393, `superseded` 58,
`in-progress` 15 and `blocked` 4. The consumer's cut skips `superseded` rows as closed
(`platform/review-loop/cut.py:21`). With this change `check_spec.py` refuses each of the 83 delivered FEATs until it
carries the legacy line, and `spec_trace.py status` reports one FEAT: FEAT-076 is `delivered` with T25 and T26 `todo`.

[FACT] KIT-071 (PR #235) measured the `parallelize` trigger case at 0.00 over 5 runs on its branch and on `origin/main`;
Claude ran independent checks at once without loading the skill. Issue #240 sends the fan-out to `sdd-implement`.

## Change

- `sdd-implement`: the entry is the FEAT, in mode task (`FEAT-nnn Tn`), feat (`FEAT-nnn`, ready rows by wave) or fix
  (only the PR's findings, same branch and executor, until each `close_when` holds); PR unit from `pr_unit`;
  orientation by item state (issue, or TASK file under `tracker: none`), never the progress file; the seven-step cycle
  (orient, Red from the REQ example or counterexample, Green on the YAGNI ladder, Refactor, Prove by impact, Self-check,
  Deliver); `## Files widened` for existing tests only, with the falsifier that a changed assertion is a stop;
  `commits_by`; visual proof per `visual_approval`; `## Secrets to register`; a blocked row re-handed after the spec is
  fixed; an unknown failure to `investigate`. `references/task-pr.md` gains the Red section, the `proof` block, the
  executor line (`Executor: provider=… tier=… session=…`) and the fix-round stop. `references/parallel-waves.md` (new)
  holds the fan-out moved from `parallelize` § 4: wave 0 alone, one worktree per ready row, worker briefs, read-ahead
  (`read-ahead.md` moves here), the lead integrates, conflict merges keep both sides with the net-diff check, and the
  broad suite runs once on `main` per wave (a red `main` stops merges and gets a fix row).
- `parallelize` is slim: tool batching, background work, unsafe sequencing and close; its description points task
  waves to `sdd-implement`. `measure-conflicts.md` and `worktrees.md` stay, since `sdd-tasks` cites them.
- `review`: the delivery verdict runs nine ordered steps, each marked `script` or `judgment` (pin the criteria, gates on
  a clean checkout with reused records, the Red check, scope, acceptance per CA, design against the Plan, the
  `REVIEW.md` DoD, the verdict, the delta re-check); depth tiers light/standard/full by the `testing` § 6 row; findings
  carry severity, owner (`spec`, `apply`, `judgment`) and `close_when`; `review_rounds` sends a repeated criterion to
  the owner; `visual_approval` and `owner_approvals` hold the verdict. It never fixes or pushes: an `apply` finding
  carries its patch for the fix round (P1). `references/delivery-steps.md` (new) holds the commands, the clean-checkout
  rules, Claude `/code-review`, closure records and the verdict format; `references/coordination.md` (new) holds one
  coordinator per delivery, blocker classes A/B/C (escalate at the second same-class failure), green `main` per wave,
  conflict merges, batch review (coherence and dead code across a batch), planned versus measured evidence and
  owner-only approvals.
- `platforms/tools/review_checks.py` (new): `red` copies the PR's added or changed test files onto the base, runs them
  there and on the head, and classifies each failing test from JUnit reports or the unittest/pytest text (a case
  naming no test file of the run, such as another runner's report quoted in a message, is skipped): Red is one
  test failing on an assertion, or on a compile or import error whose missing symbols the PR's non-test diff all adds
  (the normal Red of a new class); a PR with no non-test change under the code roots is exempt without a run; a
  runtime error, every test passing on base despite a production change, or a Red made only of data entries is
  flagged (exit 3) for the reviewer, never a block on its own; it judges per PR and reports per test. `scope` checks
  the Files cell, `## Files widened` (existing tests only, no changed assertion) and `protected_paths` labels; `proof`
  checks the `## Red` section, the `proof` block and the executor line and re-runs allowlisted proof lines;
  `feat-proofs` re-runs every command of a FEAT's Proof cells. Both re-runs check each named path first (a moved file
  is a stale proof) and fail a run whose output matches its stack's failure pattern even at exit 0, from a per-stack
  table (`godot`, `maven`, `python`) that a project extends with `--patterns`; the `maven` lint flags `-Dtest` with
  `verify`. `dod` matches the `REVIEW.md` lines ending in `<!-- grep: REGEX -->` (or `grep tests:`) and dropped
  assertions. Scope and allowlist rules are imported from `pr_gates.py`, so the CI gate and the local tool agree.
- `sdd-review` (new, step 8), trimmed by the calibration: after the last row merges, on a clean `main`, by a context
  that delivered no row. Scripts first: the start gate (`spec_trace.py validate --check`), `review_checks.py
  feat-proofs` on every task proof, `spec_trace.py lint` (new: "Not verified" or an Audit still "Pending", `[PROPOSAL]`
  in Scope, `[HYPOTHESIS]` in Open questions or a done row, "until/once Tn" with Tn done, a Plan row count that differs
  from the table, and each listed REQ's proving test missing from its trace row) and the wave's broad-suite record on
  `main`; no separate re-run of each REQ's tests. Model judgment only on what they flag: re-pointing stale proofs (and
  re-running only those), rewriting stale markers, folding a flagged `[DECISION]` with a `→ folded into` marker, and
  mapping each REQ example and counterexample to an asserting test, whose output is a list of missing-test rows, not a
  block on `validated` (the reading is fallible: 1 of 3 spot checks was wrong); REQ-NF measurements and a touched
  journey's manual checks stay. Outcomes `validated` or a row, `sdd-clarify`, a NEED fix or a DEBT; the `## Closure`
  record with retro numbers, `references/closure-record.md` (with the calibration and its falsifier).
- `sdd-release` (new, step 9): group validated FEATs, changelog and version (`git` § 9), deploy to the test environment
  and smoke, the owner's acceptance (playtest or captures against the mock), flag on with a written rollback plan,
  `spec_trace.py deliver` (FEAT and complete NEEDs `delivered`), feedback to `sdd-intake` as child NEEDs; under
  `release: merge` it changes no status.
- Statuses: `spec_trace.py status` derives `in-progress` at most and fails a validated or delivered FEAT with an open
  row (`done`, `superseded` and KIT-068's `cancelled` close a row); `validate` (rows closed, a `## Closure` record,
  every step of a journey that a NEED listing the FEAT names filled) writes `validated`, or `delivered` under
  `release: merge`; `deliver` writes `validated → delivered`; both append a History line and move each NEED whose
  FEATs are all delivered and cover its REQs. `check_spec.py` (rule `feature-closure`) requires that line on a
  validated or delivered FEAT, or `delivered before sdd-review` on one delivered under the old derivation. This
  closes the KIT-066 follow-up: a journey step citing no REQ can no longer keep `—` once its FEAT closes.
- `sdd-process.md` (chain, Flow, table rows 6–9, status owners), `spec-feature.md` (status comment, `## Closure`),
  `spec-need.md` (who sets `delivered`), `platforms/kits/github/REVIEW.md` (blocker classes, the Red line, a grep-able
  weak-test line), `platforms/kits/github/PULL_REQUEST_TEMPLATE.md` (Red, Proof, executor line), `testing` § 2 (the
  failing line goes to `## Red`), `sync-profiles.txt` (both new skills to the docs profile), `platforms/tools/README.md`,
  `platforms/ci/README.md`, `INDEX.md`.

Consumer adoption: a project resyncs, then adds `- YYYY-MM-DD delivered before sdd-review` to each FEAT already
`delivered`, or, while it has no `docs/spec/baseline.json` yet, runs `check_spec.py --baseline-init` once so the new
baseline holds those `feature-closure` findings (each legacy line added later shrinks it). `--baseline-init` refuses
once the file exists (`check_spec.py`: the baseline only shrinks, and `--baseline-update` only lowers it), so a project
that already has a baseline adds the legacy lines. Otherwise `check_spec.py` refuses those FEATs; FEATs at `in-progress` with every row done stay there until `sdd-review`.

After KIT-068 (#244) merged: `session/references/handoff-record.md` and `templates/doc-session-handoff.md` read the
rows' items (issues, or TASK files) instead of the progress file, which stays only for FEATs cut before KIT-068.

Not changed, follow-ups: `pr_gates.py` keeps `protected_paths` as label → globs while `sdd:` holds path →
label; the coordinator re-ran the `parallelize` trigger case of KIT-071 at `76f1198`: 0.00 (0 of 5), the same as on
`main`, so the trigger question moves to KIT-070. `derived_status` still ignores `doing` rows, a gap inherited from
`main`: #247.

## Calibration

The owner's adjustment 2: `KIT-069-CALIBRATION-2026-11-14.md` (read-only measurement session, consumer `main`
`606a2f6f9`); the coordinator turned its recommendation into decisions for this PR (2026-11-15).

- [FACT] Closure on 5 delivered FEATs: every FEAT had findings and none was a product defect; 0 of 3,263 server and client
  tests failed. 3 of 5 FEATs had a proof rotted by a later PR (a merged folder, a renamed content id, a moved Godot
  script whose `-s` run exits 0 after `Can't load script`); 3 Maven rows ran `-Dtest=… verify`, which runs every IT.
  Reading found 16 stale-text items over 5 of 5 FEATs; 4 counterexample clauses were untested, 5 partly covered and 2
  weakly of 61, and 1 of 3 grep spot checks of an "untested" claim was wrong; REQ-F-997's trace row listed no test.
- [FACT] Red check on the 10 latest merged PRs that change tests: 6 fail on base on an assertion, 2 only on a compile
  error naming the class the PR adds (#4371, #4280), 2 are test-only and pass on base by construction (#4056, #4048);
  all 10 pass on head. An assertion-only rule would have blocked 4 sound PRs; the classifier above blocks none. Cost:
  one extra base build per PR (server 21–81 s, client import 4–28 s plus the suite).
- [FACT] `spec_trace.py lint` on the same 5 FEATs at consumer `8549f51d4`: 20 stale-marker and 26 trace findings
  (FEAT-109: "Not verified", Audit "Pending", 3 `[PROPOSAL]` Scope bullets, the `[HYPOTHESIS]` row-size question, a
  `[HYPOTHESIS]` in done row T6, "until T5" with T5 done, and REQ-F-997 with no test in its trace row). As an audit over
  every delivered FEAT it reports 1,085 findings, 758 of them trace gaps, so it runs per FEAT at closure, not in CI.
- [FACT] `review_checks.py feat-proofs --feat FEAT-109` without `--run` (lint only, nothing executed) flags T2, T3 and T9,
  the three `-Dtest=… verify` rows the report found by hand.
- [FACT] History-split lint (added in the review round): it flags a bullet that stops mid-sentence, followed by one or
  more complete bullets (each ends a sentence or is a line the tool writes) and then an indented line. The cause was
  the insertion point of `append_history` (after a bullet's first line), which now goes past the bullet's continuation
  lines. On the closed consumer FEATs at `8549f51d4` it flags 38 bullets in 33 FEATs, among them the report's FEAT-084,
  FEAT-097, FEAT-063 and FEAT-099. An earlier rule (one inserted line, then a wrap-width bound) found 28 of them and
  missed the 10 where 2 to 10 `done` lines landed inside a wrapped bullet: FEAT-004:558, FEAT-005:422 and :427,
  FEAT-014:128 and :138, FEAT-017:211, FEAT-021:140, FEAT-024:576, FEAT-026:198 and FEAT-058:2057. A one-line bullet
  merely left unterminated is not flagged, because the wrapped bullet after it is incomplete and owns the indented
  line: consumer FEAT-030:611 at `d23561cba`, a 226-character bullet the first rule flagged. At `d23561cba` the closed
  FEATs give 18 hits, FEAT-030:611 not among them.
- Dropped, with the reason: a lint for an unfolded `[DECISION]` in Open questions flags 676 lines over 91 consumer FEATs
  (18 on the five calibration FEATs), because the consumer answers questions in place with `[DECISION]`; the report's
  one real unfold was a `[PROPOSAL]` left in Scope, which the Scope lint reports, so `sdd-review` folds what that lint
  flags and has no `[DECISION]` step. The content-id check is dropped from the kit: the content pack is a consumer
  artifact the kit does not model, so the consumer's own content tooling owns it.
- Falsifier: a larger sample (the report proposes 20 FEATs and 30 PRs) in which the dropped REQ re-run finds a real
  `main` failure that the wave's broad suite missed, or a PR whose tests all pass on base yet hide a defect.

## Proof

`bash platforms/tools/check.sh` (also with `CI=1`), `bash platforms/tools/smoke.sh`,
`python3 platforms/ci/validations/check_kit.py --links`, the `test_check_spec`, `test_spec_trace` and
`test_sync_project` suites, the new `test_review_checks`, `test_check_spec_closure` and `test_spec_trace_closure`
suites, and `gitleaks git --redact --log-opts=origin/main..HEAD`. Tests first: on `22aa841` (tests only, the code of
`540b6d5`) 39 of the 47 new or changed tests fail. The 8 that pass there: 5 assert that a valid record passes, which
the old checker allows because it checks none; 1 asserts a validated or delivered FEAT is not rewritten by its rows,
which the old derivation also kept; 1 asserts a usage error exits 2, which a missing script also does; and 1 counts
worktrees, which a missing script leaves unchanged. The calibration round's tests (`b15feda`: 9 Red classifier, 4
proof-output and 2 `feat-proofs` cases in `test_review_checks`, 14 in the new `test_spec_trace_lint`) all 29 fail
against `27b0ce7`'s tools and pass after. The first run on the consumer's spec treated `superseded` as open
(50 failures over 11 FEATs); the 2 tests added for it fail against `bf29c83`'s `spec_trace.py` (3 failures with
subtests) and pass after the fix. Running `red` on this PR itself read unittest's `FAILED (failures=1)` summary as a
test and classed an assertion failure by a missing symbol quoted in its message; the 3 tests for it (`10615f7`) fail
against `0855809`'s tool and pass after. Results are in the PR body.

## History

- 2026-11-14: confirmed (owner, chat): the acceptance, review and release design ("concordo"), the six further
  adjustments ("Aprovo todos"), and this run with its merges ("orquestre a implementação de tudo que passamos", "Já
  libero todos os merges. Faça tudo com autonomia pra entregar").
- 2026-11-15: calibration folded in (coordinator's decisions from the calibration report): `sdd-review` trimmed to
  scripts plus flagged judgment, the Red classifier, per-stack output checks and lints, `spec_trace.py lint`.
- 2026-11-15: merged with KIT-068 (#244, coordinator's list): the closure rule id `feature-closure` in `RULES`, the
  legacy line in #244's delivered fixture, `sdd-process.md` without `sdd-to-card`, item-state wording in
  `spec-feature.md` and the handoff record; `cancelled` rows close like done ones (found by the merge).
- 2026-11-15: coordinator review of `5a4b780` (PARTIAL, 13 findings) fixed: a refused release reopens a validated FEAT
  (`status --write`); `red` takes per-stack commands from the gates config (`{classes}`, `{-a res}`) and reads a run
  with no test as an ERROR; rules files are read from base; `&` separates proof commands (`pr_gates.py`, Files widened
  by the coordinator); runs are process groups; `res://` follows `--path`; the History-split lint; the `[DECISION]`
  lint and the content-id check dropped with their reasons.
- 2026-11-15: coordinator delta review of `8ec83eb` (PARTIAL) fixed: a rules file the head deletes or links to
  `/dev/null` or outside is still read from base (`dod` defaults to base's `REVIEW.md`; `scope --gates` too); Ctrl-C
  kills a run's process group; the History-split lint skips tool-written lines and lines wider than the FEAT wraps (0
  false positives left at `d23561cba`, so it stays blocking); `&>/dev/null` is a safe redirect; `{classes}` stems are
  shell-quoted; a parity test pins the two closure-line readers; `--baseline-init` applies only before the first
  baseline; `spec-index.md` status wording (Files widened by the coordinator).
- 2026-11-15: coordinator delta review of `76f1198` (PARTIAL) fixed. A rules file whose folder resolves inside the
  repository (the leaf is not resolved) is always read from git as base has it, never from the checkout; this closes
  the alias-path loosening and the crash on a deleted file. SIGTERM and SIGHUP kill a run's process group. The
  History-split lint takes any number of inserted complete bullets and drops the width rule (`8549f51d4`: 28 to 38
  hits, the 10 added all real). Run output that is not UTF-8 is decoded with replacement. The `parallelize` trigger
  eval, re-run by the coordinator, moves to KIT-070; `doing` rows in `derived_status` are #247.
- 2026-11-15: coordinator delta review of `17cc61d` (PARTIAL) fixed. The three rules-from-base fixes each resolved part
  of the path through the head checkout, which the PR controls (the leaf, nothing, then the parent folder with
  `realpath`, which follows a committed folder link). Now only the part in front of the repository is resolved: the
  shortest prefix that is the repository's folder ends it and the rest stays lexical, so no committed link moves the
  path. A rules path that names a folder exits 2; diff text that is not UTF-8 is decoded with replacement.
- 2026-11-15: the four sibling holes, coordinator's call on `ca13b6c` (the head decided what the checks see): an
  in-repo `--patterns` file is read from base like `--gates` and `--review` (`proof` needs `--base` for one); diffs
  use raw file names (`core.quotePath=false`, C-quoting decoded, `-z` for name lists) and `--text --no-textconv
  --no-ext-diff`; a deleted test file's assertions count as dropped, a rename (`-M`) does not. Found while rewriting
  the parser: an added line `++ x` read as a file header hid the rest of its file; headers are now read only between
  `diff --git` and the first hunk.
- 2026-11-15: coordinator review of `3ef926b` (BLOCKED) fixed. The parser holes shared one premise: git's patch text
  was trusted for its line structure and headers. git output is now read as bytes and split only on `\n` (a CR, FF or
  U+2028 inside an added line had reopened header mode, and a CR-only file lost every line after its first);
  `changed()` lists names with `--no-renames`, so a move shows its old, possibly protected, path; a test file moved out
  of the test globs drops its assertions; diffs fix `--src-prefix=a/ --dst-prefix=b/`; a base rules file the tool
  cannot read exits 2. Not here: #248 (a rename that leaves the runner's discovery pattern), #249 (`feat-proofs` needs
  `--base` like `proof`).
- 2026-11-15: coordinator review of `f5da22d` (BLOCKED) fixed. One line rule: patch lines split on `\n` drop one
  trailing `\r` (a `$`-anchored rule missed every CRLF line), and files read whole split on CRLF, CR or LF (a CR-only
  REVIEW.md had collapsed into one rule). A test moved out of the test globs is read at the merge base, not base's tip
  (a crash when base had deleted it, a wrong count when base had edited it). The widened-assertion check follows a
  rename back to the widened path. A config value of the wrong type, or any crash, exits 2 through a top-level
  handler, and `--patterns` regexes and shapes are checked up front. Not here: #250 (`feat-proofs` rows split on FF,
  NEL or U+2028), #251 (`pr_gates` splits PR bodies on CommonMark line endings only), #252 (value types in the gates
  and patterns config).
- 2026-11-15: coordinator review of `1cfd58a` (BLOCKED, one item) fixed: `rules_text` verifies the rev it reads rules
  from (`git rev-parse --verify --quiet <rev>^{commit}`); a rev that is not a commit (a shallow CI clone without the
  base) or a `--repo` that is no git repository exits 2 instead of reading as "not on base", which had dropped base's
  patterns. The exit-2 claims now cover only configs the tool cannot read or use (#252 for types); `dod` does not see
  line-ending CRs. Not here: #253 (a PR-controlled crash as a finding), #254 (CR-only test files in the assertion
  count), #255 (an import error and `--timeout 0`).
- 2026-11-21 (amendment, from the Stratics FEAT-038 closure, stratics#5256): `spec_trace.py lint` skips a REQ with
  `status: retired` when it checks proving tests against the trace, since a decision removed its rule and tests (REQ-F-814,
  DTEC-061 § 3). The Maven proof lint in `review_checks.py` no longer flags `-Dtest=... verify` when the line also
  holds `-Dit.test=`, which narrows failsafe (T5, T11). A Proof cell with no command (T15's retirement note) stays an
  informational `not run` line, not a finding. Tests: `test_a_retired_req_needs_no_proving_test_in_the_trace`,
  `test_maven_verify_narrowed_by_it_test_is_not_linted`.
- 2026-11-22 amend (#435): validate requires the closure's outcome line and one check row with a measured Result; a placeholder closure (Stratics FEAT-147) no longer passes the start gate.
- 2026-11-22 amend (#453): closure validation splits pipes outside backtick spans, counts only rows under the Shape check-table header, and refuses any `not run` Result with `outcome validated`; delivered and returned closures still allow it.
