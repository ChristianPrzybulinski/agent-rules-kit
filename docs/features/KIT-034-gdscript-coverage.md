---
id: KIT-034
title: "GDScript line and branch coverage per function, from our own probe instrumenter"
status: confirmed
confirmed: "2026-11-10 (owner, ub-mode evaluation decisions D3 and D5 in the chat of the ub-mode evaluation session; implementation prompt launched 2026-11-11)"
issue: "#136"
pr: ""
---

# KIT-034 — GDScript line and branch coverage per function, from our own probe instrumenter

## Problem and evidence

The owner evaluated the ub-mode principles against the kit on 2026-11-10
(`/Users/christian/Developer/GitHub/PROPOSAL-UB-MODE-2026-11-10.md`, the parity rows and build order at lines
127–133 and § 5 "KIT-033 — GDScript coverage (ours)" at lines 258–268, which this feature implements under its real
id). The kit builds its own GDScript tools instead of running third-party ones (D3), and every quality check one
language has, the other gets (D5). This PR holds the feature docs and the measured T1 spike only; the owner decides on
T2 and later from the T1 numbers. Facts re-checked at kit `49b2137` and stratics-client `f98e0091`:

- [FACT] the same rule gets a coverage gate in Java and none in GDScript.
  `plugins/dev-core/skills/testing/SKILL.md:19`: "Domain rules involving business logic, money, inventory, rewards,
  battle or authorization require 100% line and branch coverage plus mutation score ≥80%. These gates are never
  reduced." Line 23: "GDScript (Godot): no line, branch or mutation percentage gate; the tooling does not exist."
  `plugins/dev-godot/skills/godot-standards/references/testable-game-logic.md:28`: "Coverage policy: every game rule
  has a scene-free test; there is no numeric gate for GDScript." Java has the JaCoCo and PIT rows of
  `plugins/dev-java/skills/java-standards/references/build-and-dependencies.md:35`–`36`.
- [FACT] the test runner has no coverage: `grep -rni coverage addons/gdUnit4` in the client matches one line,
  `src/core/attributes/TestCaseAttribute.gd:54` "Higher values provide better coverage but increase test duration.",
  a fuzzing comment (gdUnit4 6.2.1, proposal line 37).
- [FACT] the client's own test command is `tools/dev.sh:40`–`42`: `godot --path . --headless --import`, then
  `godot --path . --headless -s addons/gdUnit4/bin/GdUnitCmdTool.gd -a res://tests -c --ignoreHeadlessMode`. `-c` is
  `--continue` (`addons/gdUnit4/src/core/runners/GdUnitTestCIRunner.gd:46`, `disable_fail_fast` at line 343).
- [FACT] the runner's exit code alone does not prove a run: "No test cases found, abort test run!" exits
  `RETURN_SUCCESS` (`GdUnitTestCIRunner.gd:394`–`396`), and script errors found during discovery exit 105
  (`GdUnitTestSessionRunner.gd:23`, `GdUnitTestCIRunner.gd:384`–`390`); 100 is a failure and 101 a warning (lines 20
  and 24).
- [FACT] the parser needs no new dependency: `gdtoolkit==4.5.0` is pinned at
  `platforms/kits/godot/requirements-gdtoolkit.txt:2`, and `gdtoolkit.parser.parser.parse(text, gather_metadata=True)`
  gives every statement its line and column.
- [FACT] the consumer is waiting for it: KIT-031 (#133, branch `feature/kit-031-complexity-signal`, not merged) adds
  `platforms/tools/complexity.py`, whose docstring (line 10) says "GDScript coverage (KIT-034) only has to fill
  `Function.coverage`"; `Function.coverage` is line 45 and the CRAP formula
  `self.cc ** 2 * (1 - self.coverage) ** 3 + self.cc` line 50.

## Change

This PR adds this file, its row in `docs/features/README.md` and one CHANGELOG line. No tool, skill or gate changes
until the owner approves T2.

The tool it specifies, `platforms/tools/gd_coverage.py` (Python 3.9+, gdtoolkit 4.5.0, our own code, D3):

1. **Copy.** `git archive <ref>` of the project into a new `mktemp -d` folder; the source checkout is never edited.
   The copy runs `godot --path <copy> --headless --import` first, because a fresh checkout has no class-name cache
   (`tools/dev.sh:38`–`40`).
2. **Instrument.** Every `.gd` file of the copy outside `addons/`, `tests/` and `.godot/` is parsed with gdtoolkit and
   gets probes inserted at the line and column of the statement they precede. Only text goes in, never a newline, so
   every line number of the copy is the source's. Three kinds of probe:
   - *block*: the entry of the first statement of each function body, `if`/`elif`/`else` arm, `for`/`while` body and
     `match` arm;
   - *continuation*: the statement right after a compound statement (`if`, `for`, `while`, `match`) in its block, so a
     line after an `if` whose arm returns is not counted from the block's entry;
   - *condition*: each `if`/`elif`/`while` condition becomes `KitCov.b(N, <condition>)`, which counts the true outcome
     in slot N and the false one in N + 1 and returns the value unchanged.

   A simple statement takes `KitCov.hit(N); ` in front. A compound statement never does: an `if` entry is the sum of
   its first condition's two outcomes, a `for` or `match` entry wraps its iterable or subject as `KitCov.v(N, …)`, and a
   `while` entry is not measured (its condition runs once per iteration). Lambdas are not entered.
3. **Record.** The copy gains `kit_cov/kit_cov.gd` (`class_name KitCov`, a static `PackedInt64Array` of hit counts) and
   an autoload `kit_cov/kit_cov_writer.gd`, added first under `[autoload]` of the copy's `project.godot`, that writes
   `{"reason", "hits"}` to `$KIT_COV_OUT` once, on `_exit_tree` with `NOTIFICATION_PREDELETE` as the fallback. If the
   autoload proves unreliable under `GdUnitCmdTool`, the writer moves to a gdUnit4 session hook (project setting
   `gdunit4/hooks/session_hooks`, `addons/gdUnit4/src/core/GdUnitSettings.gd:14`–`15`, base class
   `src/core/hooks/GdUnitTestSessionHook.gd`).
4. **Run.** The project's own test command on the copy, with `HOME` pointed at a scratch folder so `user://`, the
   editor settings and the logs stay out of the owner's home. A run counts only when it exits 0 or 101 and its
   "Overall Summary" line shows one test case or more; otherwise the tool prints why and reports no coverage.
5. **Report.** JSON per function: path, name, first and last line, covered and total statement lines (the first line of
   each statement; a line is covered when the probe that enters its run of statements counted at least once), taken
   and total branch outcomes (two per `if`/`elif`/`while` condition) and the uncovered lines. `--base REF` limits the
   report to the functions whose lines changed, read the same way as `complexity.py`. Exit 0 (advisory); a gate waits
   for T7.
6. **CRAP.** `complexity.py` reads that JSON and fills `Function.coverage` with the line ratio for GDScript, so a
   GDScript function scores CRAP the way a Java one does from JaCoCo (T5).

`plugins/dev-core/skills/testing/SKILL.md:23` and `testable-game-logic.md:28` change only in T6, after the tool exists.
No CI or loop gate runs it (D2, D5).

## Tasks

| Task | What | Done when |
|---|---|---|
| T1 | Spike on `app/update/pack_choice.gd` and `tests/update/pack_choice_test.gd`: instrumentation time, plain and instrumented test time, hit counts against a hand count, plus one whole-project instrumentation | the numbers are in § Measurements (this PR) |
| T2 | `gd_coverage.py` instrumenter and `platforms/ci/validations/test_gd_coverage.py` (parser cases `skipUnless` gdtoolkit, as CI does not install it): probe placement, unchanged line numbers, the output parses again, one-line `if`, lambdas, `@tool` scripts, property accessors, `match` arms as branch outcomes | tests green; INDEX rows in `platforms/tools/INDEX.md` and `platforms/ci/validations/INDEX.md` |
| T3 | Recorder and writer, with the session-hook fallback if T1 or T2 shows the autoload missing a run | the hits JSON is written on a passing run, a failing one (exit 100) and one with orphans (exit 101) |
| T4 | Runner, per-function JSON, `--base` for changed functions; the whole client suite instrumented | one full suite run with no instrumentation failure, and its time |
| T5 | `complexity.py` fills `Function.coverage` for GDScript from the T4 JSON (needs KIT-031 merged) | a GDScript function reports CRAP in `test_complexity.py` |
| T6 | `testing` § GDScript and `testable-game-logic.md:28` name the advisory command; one eval case that does not name its skill; descriptions unchanged | `check.sh`, the eval and the skill size caps pass |
| T7 | Overhead and false-positive rate over two loop batches; the owner decides on a gate (proposal line 284) | numbers in § Measurements and an owner decision |

KIT-035 (GDScript mutation) uses T4's covered lines to pick its mutants. The PR of the last task the owner approves
closes #136; this PR refers to it.

## Decisions

- 2026-11-11 T1 (#144): chose block and continuation probes over one probe per statement because a run of simple
  statements has a single entry: `pack_choice.gd` needed 70 probes in 72 counter slots for its 54 statement lines,
  and 14 of the entries are read from a condition's two outcomes instead of a slot of their own.
- 2026-11-11 T1 (#144): chose no probe in front of a compound statement over a `KitCov.hit(N); ` prefix because `;`
  joins only simple statements: gdtoolkit 4.5.0 parses `var a = 1; print(a)` and rejects `var a = 1; if a: pass` and
  `KitCov.hit(1); for i in [1]: pass` with `UnexpectedToken`.
- 2026-11-11 T1 (#144): chose no branch outcome for a `for` loop over counting empty and non-empty iterables, open for
  T2, because the entry probe on its iterable already shows whether the loop line ran; `match` arms become branch
  outcomes in T2.
- 2026-11-11 T1 (#144): chose `HOME` pointed at a scratch folder over editing the copy's settings because the spike
  confirmed it: the real `godot.log` kept its mtime and every run logged under the scratch `HOME`.
- 2026-11-11 T1 (#144): chose the writer autoload over a gdUnit4 session hook because it wrote the hits JSON on
  `_exit_tree` in all 4 instrumented runs; the hook stays T3's fallback.
- 2026-11-11 T1 (#144): chose the statement-line ratio for `Function.coverage` over the branch ratio because KIT-031's
  `complexity.py:7` reads JaCoCo's INSTRUCTION counter for Java, and a statement is GDScript's nearest unit to an
  instruction.
- 2026-11-11 T1 (#144): chose "Refs #136" over "Closes #136" because `docs/maintenance.md:18` says "the implementing
  PR closes the issue" and this PR implements T1 only.

## Risks

- [FACT] one-line compound statements (`if x: return y`): the client has none outside `addons/` and `tests/` at
  `f98e0091` (a `git grep` for `if`, `elif`, `else`, `for` or `while` with a body after the colon), so no T1 run put a
  probe after a colon; T2's tests cover it.
- [FACT] lambdas are not entered; 106 lines in 43 client files hold one. [HYPOTHESIS] their body lines read as
  uncovered unless the report leaves them out (T2).
- [FACT] `@tool` scripts: the client has one, `features/trade/trade_add_button.gd`, and the instrumented whole-project
  `--import` exited 0 with no parse error in its log. [HYPOTHESIS] that does not show the script ran inside the import
  with `KitCov` known.
- [FACT] the `.godot` import cache: the copy that gained `class_name KitCov` always ran one more `--import` (3.16 s for
  one file, 3.61 s for the whole project); a run without it was not tried. Mutated function bodies loaded with no new
  import: KIT-035 T1 shows a compile error at line 58 and a runtime error at line 48, the mutated lines.
- [FACT] `user://` isolation through `HOME` holds on macOS: the real
  `~/Library/Application Support/Godot/app_userdata/Stratics/logs/godot.log` kept mtime 1794305802.564249 across the
  spike, and the runs wrote their logs under the scratch `HOME`.
- [HYPOTHESIS] property `get`/`set` bodies and class-level `var` initialisers are not function bodies in the gdtoolkit
  tree, so they get no probe.
- [FACT] a `while` loop's entry is not measured, and the operands of `and`/`or` are not separate outcomes: the
  condition probe counts the whole condition.

## Measurements

T1 ran on 2026-11-11 from 10:11:53 to 10:12:43 (50 s for the whole driver, KIT-035 T1 included) on a `git archive`
copy of stratics-client `f98e0091` in a new `mktemp -d` folder; nothing in `stratics-client` was edited. Godot
4.7.2.stable.official.ed1daf0bf ran headless under `nice -n 10` with `HOME` at a scratch folder; the load average was
3.49 at the start, with fewer than 2 loop gate runs on the host. The spike's scripts (instrumenter, report, hand count
and driver) live in the session's scratchpad, not in the kit.

| Step | Time |
|---|---|
| `git archive` and extract | 1.24 s |
| first `--import` of the copy | 12.08 s, exit 0 |
| APFS clone (`cp -cR`) of the imported copy | 2.53 s and 2.38 s |

One file, `app/update/pack_choice.gd` (88 lines, 4 functions), against `tests/update/pack_choice_test.gd` (8 test
cases):

| Measure | Result |
|---|---|
| instrumentation | 0.16 s in the script, 0.27 s with Python start-up; 70 probes (4 function, 26 block, 20 continuation, 20 condition) in 72 counter slots |
| `--import` after instrumenting | 3.16 s, exit 0 |
| test run, plain (3 runs) | 0.94, 0.95 and 0.94 s; 8 test cases, 0 errors, 0 failures, exit 0 |
| test run, instrumented (3 runs) | 0.94, 0.94 and 0.84 s; the same summary, exit 0 |
| hits JSON | written by the autoload on `_exit_tree` in all 3 runs; the 3 files are identical: 56 of 72 slots non-zero, 283 hits |
| hand count | 66 probes (26 block, 20 continuation, 20 condition) against a count written from the test file before any run: 0 mismatches |

The overhead is not measurable at this size: Godot's start-up dominates a sub-second run, and the instrumented runs
fall inside the plain runs' spread. The report, identical in the 3 runs:

| Function | Statement lines | Line coverage | Branch outcomes |
|---|---|---|---|
| `check` (line 11) | 28/34 | 82.4 % | 22/28 |
| `cached` (line 62) | 12/13 | 92.3 % | 7/8 |
| `_is_integer_value` (line 78) | 3/3 | 100 % | 2/2 |
| `_matches` (line 84) | 3/4 | 75.0 % | 1/2 |
| total | 46/54 | 85.2 % | 32/40 |

The 8 uncovered lines are guard returns no test reaches: `return "SHAPE"` at lines 16, 26, 40, 42 and 46,
`return "SIGNATURE_SHAPE"` at 54 and `return false` at 70 and 87. The 8 untaken outcomes are the true outcomes of the
conditions that guard them (lines 15, 25, 39, 41, 45, 53, 69 and 86).

Whole project, on a second clone of the imported copy:

| Measure | Result |
|---|---|
| instrumentation | 257 files, 0 failed, 4.97 s in the script (5.02 s with start-up); 19,088 probes in 250 files (2,833 function, 8,451 block, 3,772 continuation, 4,032 condition) in 18,075 counter slots |
| `--import` | 3.61 s, exit 0, no parse error in its log |
| the same test file | 1.16 s; 8 test cases, 0 errors, 0 failures, exit 0 |
| hits JSON | on `_exit_tree`; 127 slots non-zero, 791 hits, in 19 of the 250 files |

The 19 files are `pack_choice.gd`, with the same 56 slots and 283 hits as the one-file runs, and 18 that the start-up
reaches through the autoloads: `audio_director.gd` 18 slots, `button_feedback.gd` 10, `ui_kit.gd` 8, `chat_log.gd`
7, `network.gd` 6, `session.gd`, `session_upkeep.gd` and `toast_layer.gd` 4 each, and 10 others 1 each, with no
script error. A test run loads only the scripts it reaches, so whether the other 231 files with probes compile is
T4's full-suite question.

## Proof

Run from the worktree root at `3bdba5c` on 2026-11-11 (the commits after it change only this document and
`docs/features/README.md`); every command exited 0:

- `bash platforms/tools/check.sh` and `CI=1 bash platforms/tools/check.sh`: "check: OK (14 plugins, 46 skills, 3 rules,
  22 templates, 23 indexes, 123 links, 25 hook cases)", then "✔ Validation passed" 15 times and no skip line.
- `bash platforms/tools/smoke.sh`: "smoke: OK (46 skills, app fallback, cleanup, symlink safety, manifests,
  sync-project, rules copy, vendored skills, multi-profile sync, no-spec repo)".
- `python3 platforms/ci/validations/check_kit.py --links`: "check: OK (14 plugins, 46 skills, 3 rules, 22 templates, 23
  indexes, 123 links, 25 hook cases)".
- `gitleaks git --redact --log-opts="origin/main..HEAD"`: "1 commits scanned.", "scanned ~16577 bytes (16.58 KB) in
  50.8ms", "no leaks found".

## History

- 2026-11-10: confirmed (owner, ub-mode evaluation decisions D3 and D5).
- 2026-11-11: implementation prompt launched; issue #136; T1 spike run.
- 2026-11-11: specification and T1 spike in #144, which refers to #136 and leaves it open.
