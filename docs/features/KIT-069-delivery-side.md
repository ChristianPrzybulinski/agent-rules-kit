---
id: KIT-069
title: "The delivery side of the SDD flow: implement modes and task cycle, review steps backed by scripts, sdd-review closes a FEAT, sdd-release delivers it"
status: confirmed
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
- `platforms/tools/review_checks.py` (new): `red` copies the PR's added or changed test files onto the base and expects
  a failure there and a pass on the head, printing the base failure for the reviewer to judge; `scope` checks the Files
  cell, `## Files widened` (existing tests only, no changed assertion) and `protected_paths` labels; `proof` checks the
  `## Red` section, the `proof` block and the executor line and re-runs allowlisted proof lines; `dod` matches the
  `REVIEW.md` lines ending in `<!-- grep: REGEX -->` (or `grep tests:`) and dropped assertions. Scope and allowlist
  rules are imported from `pr_gates.py`, so the CI gate and the local tool agree.
- `sdd-review` (new, step 8): after the last row merges, on a clean `main`, by a context that delivered no row: the
  start gate (`spec_trace.py validate --check`), every CA, each delivered REQ's example and counterexample, each REQ-NF
  measurement (metric, target, measured), the touched journeys end to end, stale proofs found and re-pointed, settled
  decisions folded with a `→ folded into` marker and resolved conditionals rewritten; outcomes `validated` or a row,
  `sdd-clarify`, a NEED fix, or a row or DEBT; the `## Closure` record with retro numbers (blocked rows, review rounds,
  REQs amended after `planned`), `references/closure-record.md`.
- `sdd-release` (new, step 9): group validated FEATs, changelog and version (`git` § 9), deploy to the test environment
  and smoke, the owner's acceptance (playtest or captures against the mock), flag on with a written rollback plan,
  `spec_trace.py deliver` (FEAT and complete NEEDs `delivered`), feedback to `sdd-intake` as child NEEDs; under
  `release: merge` it changes no status.
- Statuses: `spec_trace.py status` derives `in-progress` at most and fails a validated or delivered FEAT with an open
  row (`done` and `superseded` close a row); `validate` (rows closed, a `## Closure` record, every step of a journey that a NEED listing the FEAT names filled)
  writes `validated`, or `delivered` under `release: merge`; `deliver` writes `validated → delivered`; both append a
  History line and move each NEED whose FEATs are all delivered and cover its REQs. `check_spec.py` requires that line
  on a validated or delivered FEAT, or `delivered before sdd-review` on one delivered under the old derivation. This
  closes the KIT-066 follow-up: a journey step citing no REQ can no longer keep `—` once its FEAT closes.
- `sdd-process.md` (chain, Flow, table rows 6–9, status owners), `spec-feature.md` (status comment, `## Closure`),
  `spec-need.md` (who sets `delivered`), `platforms/kits/github/REVIEW.md` (blocker classes, the Red line, a grep-able
  weak-test line), `platforms/kits/github/PULL_REQUEST_TEMPLATE.md` (Red, Proof, executor line), `testing` § 2 (the
  failing line goes to `## Red`), `sync-profiles.txt` (both new skills to the docs profile), `platforms/tools/README.md`,
  `platforms/ci/README.md`, `INDEX.md`.

Consumer adoption: a project resyncs, then adds `- YYYY-MM-DD delivered before sdd-review` to each FEAT already
`delivered`, or `check_spec.py` refuses it; FEATs at `in-progress` with every row done stay there until `sdd-review`.

Not changed, follow-ups: `sdd-tasks` still writes the progress file and `session`'s handoff record still reads it
(KIT-068 replaces it with TASK files); `pr_gates.py` keeps `protected_paths` as label → globs while `sdd:` holds path →
label; the `parallelize` trigger case of KIT-071 is re-run once #235 merges here.

## Calibration

The owner's adjustment 2 measures the closure on 5 delivered consumer FEATs and the Red check on the added tests of 10
merged consumer PRs. Interim result relayed by the coordinator: 3 of the FEAT proof commands fail as written because
later PRs moved the paths they cite, so the closure finds stale proofs (`sdd-review` § 2 handles them). Each closure
check is one row type and the Red check one subcommand, so either can be trimmed when the report lands.

## Proof

`bash platforms/tools/check.sh` (also with `CI=1`), `bash platforms/tools/smoke.sh`,
`python3 platforms/ci/validations/check_kit.py --links`, the `test_check_spec`, `test_spec_trace` and
`test_sync_project` suites, the new `test_review_checks`, `test_check_spec_closure` and `test_spec_trace_closure`
suites, and `gitleaks git --redact --log-opts=origin/main..HEAD`. Tests first: on `22aa841` (tests only, the code of
`540b6d5`) 39 of the 47 new or changed tests fail. The 8 that pass there: 5 assert that a valid record passes, which
the old checker allows because it checks none; 1 asserts a validated or delivered FEAT is not rewritten by its rows,
which the old derivation also kept; 1 asserts a usage error exits 2, which a missing script also does; and 1 counts
worktrees, which a missing script leaves unchanged. The first run on the consumer's spec treated `superseded` as open
(50 failures over 11 FEATs); the 2 tests added for it fail against `bf29c83`'s `spec_trace.py` (3 failures with
subtests) and pass after the fix. Results are in the PR body.

## History

- 2026-11-14: confirmed (owner, chat): the acceptance, review and release design ("concordo"), the six further
  adjustments ("Aprovo todos"), and this run with its merges ("orquestre a implementação de tudo que passamos", "Já
  libero todos os merges. Faça tudo com autonomia pra entregar").
