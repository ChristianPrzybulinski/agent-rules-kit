---
id: KIT-034
title: "GDScript line and branch coverage per function, from our own probe instrumenter"
status: done
confirmed: "2026-11-10 (owner, ub-mode evaluation decisions D3 and D5 in the chat of the ub-mode evaluation session; implementation prompt launched 2026-11-11)"
issue: "#136"
pr: "#191, #193, #194, #196, #218"
---

# KIT-034 — GDScript line and branch coverage per function, from our own probe instrumenter

Compacted on 2026-11-16 (#291) to the problem, the decisions, the outcome and the numbers behind them. Every decision,
risk, measurement table and proof run is in the full record at `cf087f4`
([KIT-034-gdscript-coverage.md](https://github.com/ChristianPrzybulinski/agent-rules-kit/blob/cf087f4a8017f1a00e9ac57f5f39b21a6c854c51/docs/features/KIT-034-gdscript-coverage.md); `git show cf087f4:docs/features/KIT-034-gdscript-coverage.md`).

## Problem and evidence

The owner's ub-mode evaluation (2026-11-10, `PROPOSAL-UB-MODE-2026-11-10.md` § 5) set two rules: the kit builds its
own GDScript tools (D3), and every quality check one language has, the other gets (D5). Facts at kit `49b2137` and
stratics-client `f98e0091`:

- [FACT] the same rule had a coverage gate in Java (JaCoCo) and none in GDScript: skill `testing` said "GDScript
  (Godot): no line, branch or mutation percentage gate; the tooling does not exist."
- [FACT] the runner has no coverage (in gdUnit4 6.2.1 `coverage` matches one fuzzing comment), and its exit code alone
  proves no run: "No test cases found" exits 0, discovery script errors 105, a failure 100 and a warning 101.
- [FACT] no new dependency: the pinned gdtoolkit 4.5.0 gives every statement its line and column; KIT-031's
  `complexity.py` waited for GDScript coverage to fill `Function.coverage` and score CRAP.

## Change

`platforms/tools/gd_coverage.py`, advisory; its module docstring holds the mechanics and its row in
`platforms/tools/README.md` every flag. It instruments a `git archive` copy (the checkout is never edited) with probes
from the gdtoolkit tree that keep every line number, runs the project's own gdUnit4 suite once with a `KitCov` recorder
and a writer autoload, and prints `path:line function lines C/T branches C/T` per function (`--json FILE` per
statement). A run counts only on exit 0 or 101 with one test case or more and its own counters; otherwise it exits 2,
never a 0 % report. `complexity.py --gd-coverage FILE` joins the report by repository-relative path and `func` line, so
a GDScript function scores CRAP as a Java one does (T5).

T6 names the tool in skill `testing` § 1 and `testable-game-logic.md`, makes `code-standards` read CRAP for a GDScript
function a report holds, and adds eval case `testing-gdscript-coverage-command`. No CI or loop gate runs it.

## Decisions

- T1: block and continuation probes over one per statement (a run of simple statements has one entry: 70 probes in 72
  slots for 54 statement lines); no probe before a compound statement, since gdtoolkit rejects `;` before one.
- T1, T3: the writer autoload over a gdUnit4 session hook: it wrote the counters in all 4 T1 runs and on exit 0, 100
  and 101 in T3. The statement-line ratio fills `Function.coverage`, the nearest unit to JaCoCo's INSTRUCTION counter.
- T4: exit 2 for a run that does not count, so a caller never reads a missing measurement as 0 % coverage; one counter
  file per process, because client tests start Godot on the copy; `--timeout` with a process-group kill and `--exclude`
  after the first whole-suite run hung on a script a test copies out of the project.
- T4: a repeatable `--ignore SUITE` (gdUnit4 `-i`) over a list in the tool, since only the caller knows which tests
  inspect the project's own wiring and see the probes; a line only an ignored test reaches reads as not covered.
- T5: an unreadable or foreign report prints a notice and scores CC (exit 2 with `--threshold`), never 0 % coverage.
- 2026-11-13: the owner chose "Advisory only, close": no gate and T7 cancelled. The cost: no measured overhead or
  false-positive rate, so a gate proposed later starts its measurement from zero.

## Measurements

- T1, stratics-client `f98e0091`, Godot 4.7.2: `pack_choice.gd` instrumented in 0.16 s; test runs 0.84–0.94 s
  instrumented against 0.94–0.95 s plain; hit counts equal a hand count (66 probes, 0 mismatches); the whole client
  instrumented in 4.97 s (257 files, 0 failed).
- T4, the whole stratics-client suite at `310d002a` (2,749 test cases): 6 min 54 s of test time instrumented against
  6 min 6 s plain (+13 %, one run each), the same 172 script error lines, none from a probe; 3 cases that inspect the
  autoloads and dependencies fail only instrumented; 91.0 % of statement lines and 82.4 % of branch outcomes covered.
- Monorepo client at `ac649c10c`, 9 cases ignored: a counted run of 3,515 test cases in 596 s, statement lines
  24,766/26,685 (92.8 %), branch outcomes 8,310/9,860 (84.3 %). The one paired time, a run with 3 cases ignored against
  a plain copy, is +6.9 %.
- T5 on that report: 128 of 3,114 functions above the CRAP target instead of 66 by CC alone; 8 fully covered functions
  at CC 10 score CRAP 10.0, which T6's `code-standards` change closed.
- Limits: a lambda body reads as covered when its statement ran; a `while` entry is not measured, and the operands of
  `and`/`or` are not separate outcomes.

## Proof

Each PR's gates exited 0 on its head: `check.sh` (also with `CI=1`), `smoke.sh`, `check_kit.py --links`, the validation
suite, `test_gd_coverage.py` with Godot 4.7.2 and gdUnit4 6.2.1 (`KIT_GDUNIT4`), `gen_index.py --check`,
`vendor.sh --check` and `gitleaks`; T6 adds its eval case (score 1.00, one run) and the skill size caps. Output: the
full record.

## History

- 2026-11-10: confirmed (owner, ub-mode evaluation decisions D3 and D5); 2026-11-11: issue #136, T1 spike in #144.
- 2026-11-12: the owner approved T2 onward in chat ("Sim, KIT-034 primeiro"), and KIT-035 after T4 is merged. T2–T4
  and the whole client suite in #191, `--ignore` and the monorepo run in #193, T5 (`complexity.py --gd-coverage`) in
  #194, T6 (skill `testing` § 1, `code-standards` § 3 CRAP, the eval case) in #196 with KIT-035 T7; each refers to
  #136 and leaves it open.
- 2026-11-13: done: the owner kept the tool advisory with no gate ("Advisory only, close") and cancelled T7 (overhead
  and false-positive rate over two loop batches); skill `testing` § 1 now says so (#218).
- 2026-11-16: compacted to problem, decisions, outcome and numbers (#291); the full record stays at `cf087f4`.
