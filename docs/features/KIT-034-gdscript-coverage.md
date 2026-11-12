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

T1 (#144) added this file, its row in `docs/features/README.md` and one CHANGELOG line. T2–T4 add
`platforms/tools/gd_coverage.py`, `platforms/ci/validations/test_gd_coverage.py`, the tool's row in
`platforms/tools/README.md` and one CHANGELOG line. No skill or gate changes before T6.

The tool, `platforms/tools/gd_coverage.py` (Python 3.9+, gdtoolkit 4.5.0, our own code, D3), as built in T2–T4:

1. **Copy.** `git archive <ref>` (default `HEAD`) of the Godot project around the current directory goes into a new
   `tempfile.mkdtemp` folder; the source checkout is never edited. Git LFS pointers in the copy are filled from the
   local LFS store (`git rev-parse --git-common-dir`/`lfs/objects`) and never fetched; a missing object stays a pointer
   and is named.
2. **Instrument.** Every `.gd` file of the copy outside `addons/`, `.godot/`, the test folders (`--tests`, default
   `res://tests`) and each `--exclude` path (a file or folder) is parsed with gdtoolkit and gets probes inserted as
   text at the line and column of what they precede. No newline is ever inserted, so every line number of the copy is
   the source's; a file whose line count changes or that does not parse again is a failure, and a file that fails runs
   uninstrumented and is named.
   - A run of simple statements gets `KitCov.hit(N); ` in front of its first statement. A run starts at a function
     body, a property `get`/`set` body, a `for` body, a `match` arm and the statement after a compound statement, a
     `return`, `break`, `continue` or `await`.
   - Each `if`/`elif`/`while` condition C becomes `KitCov.b(N, C)`, which counts the true outcome in slot N and the
     false one in N + 1 and returns C unchanged. An `if`/`elif`/`else` arm and a `while` body are entered from that
     count, so they get no probe of their own.
   - A `for` iterable or `match` subject X that starts a run becomes `(X if KitCov.t(N) else X)`, which keeps X's
     static type; in a `range(...)` call only the first argument is wrapped, so the loop variable stays an `int`. An X
     that spans lines leaves that line unmeasured, and so does a run whose first statement carries an annotation.
   - Lambdas are not entered. Each `match` arm is one branch outcome, read from the counter that enters its body.
3. **Record.** The copy gains `kit_cov/kit_cov.gd` (`@tool`, `class_name KitCov`, a static `PackedInt64Array` of
   `SIZE` counters) and the autoload `kit_cov/kit_cov_writer.gd`, added first under `[autoload]` of the copy's
   `project.godot`, which writes `{"reason", "hits"}` to `$KIT_COV_OUT/hits-<pid>.json` once, on `_exit_tree` with
   `NOTIFICATION_PREDELETE` as the fallback. The counters of every other Godot process the tests start in the copy
   are added to the run's own. No gdUnit4 session hook is needed (§ Decisions).
4. **Run.** One `godot --headless --import` of the instrumented copy, then the project's own test command
   (`-s addons/gdUnit4/bin/GdUnitCmdTool.gd -a <tests> -c --ignoreHeadlessMode`, with `-i <suite>` for each
   `--ignore`), both under `nice -n 10` with `HOME` and the `XDG_*` folders inside the temporary folder, each in a
   process group of its own that is killed after `--timeout` seconds (default 1800). A run counts only when it
   finishes in time, exits 0 or 101, its last "Overall Summary" line shows one test case or more and its own counters
   were written; otherwise the tool prints why and the last log lines and exits 2, as it does without godot, gdUnit4
   or gdtoolkit, with a bad ref or outside a Godot project.
5. **Report.** stdout holds one `path:line function lines C/T branches C/T` line per function; `--json FILE` writes the
   ref, Godot version, test summary, exit code and `--ignore` list, timings, instrumented and failed files, LFS
   counts, probe counts and, per function, path, name, first and last line, covered and total statement lines (the
   first line of each statement; a line is covered when the probe that enters its run counted at least once), taken
   and total branch outcomes (two per `if`/`elif`/`while` condition, one per `match` arm) and the uncovered lines.
   `FILE...` limits the report to those files and `--base REF` to the functions whose lines changed in `REF...HEAD`,
   read by `complexity.py`'s `changed_lines`. `--keep` keeps the temporary folder. Exit 0 (advisory); a gate waits
   for T7.
6. **CRAP.** `complexity.py --gd-coverage FILE` (repeatable) reads that JSON and fills `Function.coverage` with the
   line ratio for GDScript, joined by repository-relative path and `func` line, so a GDScript function scores CRAP the
   way a Java one does from JaCoCo (T5); a function the report does not hold scores CC as before.

`plugins/core/skills/testing/SKILL.md:26` and `testable-game-logic.md:28` change only in T6, after the tool exists.
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
- 2026-11-12 T2: chose `(X if KitCov.t(N) else X)` over T1's `KitCov.v(N, X)` for a `for` iterable or `match`
  subject because `KitCov.v` returns a Variant: Godot 4.7.2 rejected `for i in KitCov.v(1, range(3)): var y := i + 1`
  and a `match` binding `var z` followed by `var w := z + 1` with "Cannot infer the type of "y" variable because the
  value doesn't have a set type." A ternary of two copies keeps X's type; on `range(...)` only the first argument is
  wrapped, because a ternary around the whole call also lost the `int` loop variable.
- 2026-11-12 T2: chose to count a `for` or `match` line from the run it is in over a probe of its own because a
  statement after a simple statement of the same run is reached exactly when the run is; only a `for` or `match` that
  starts a run gets `KitCov.t`.
- 2026-11-12 T2: chose to end a run after a statement that awaits (outside a lambda) over counting the lines after it
  from the run's entry because a coroutine suspended at `await` may never resume (the test ends or the object is
  freed), and those lines would read as covered without running.
- 2026-11-12 T2: chose to leave a run unmeasured when its first statement carries an annotation over a probe in front
  of the annotation because gdtoolkit 4.5.0 rejects `KitCov.hit(N); @warning_ignore("integer_division")` followed by
  the statement on the next line, and the output must parse again. [HYPOTHESIS] a probe after the annotation would
  take the annotation away from the statement it names. stratics-client `310d002a` has no indented annotation in a
  `.gd` file outside `addons/` (`git grep -P -c '^\t+@'` matches no file), so no line is lost there today.
- 2026-11-12 T3: chose the writer autoload alone over adding the gdUnit4 session hook because
  `test_gd_coverage.py` `GodotTest` runs gdUnit4 6.2.1 under Godot 4.7.2 and the autoload wrote the counters with
  `"reason": "exit_tree"` on a passing run (exit 0), a failing one (exit 100) and one with an orphan node (exit 101).
- 2026-11-12 T4: chose exit 2 for a run that does not count (an exit other than 0 or 101, no test case, no counters)
  over exit 0 with an empty report, so a caller such as T5's `complexity.py` never reads a missing measurement as 0 %
  coverage.
- 2026-11-12 T4: chose to fill the copy's Git LFS pointers from the local store (`git rev-parse --git-common-dir`,
  then `lfs/objects`) over `git lfs fetch` or leaving them because `git archive` writes the pointer files, Godot
  imports the files themselves, and a fetch is a network effect an advisory tool should not have; a missing object
  stays a pointer and the tool names the count.
- 2026-11-12 T4: chose to instrument the copy before its one `--import` over T1's import before and after the probes
  because the tool needs the copy only once: T1 paid 12.08 s for the first import and 3.61 s for the second.
- 2026-11-12 T4: chose one counter file per process, `hits-<pid>.json`, summed with the files of the other Godot
  processes in the copy, over one `$KIT_COV_OUT` file because client tests start Godot on the copy itself
  (`tests/ui/kit/kit_manifest_test.gd:339`–`346` runs `res://tools/ui/kit_import.gd` with `OS.execute`), and that
  child's writer would overwrite the run's file. The run's own file must exist: another process's never stands in.
- 2026-11-12 T4: chose a repeatable `--ignore SUITE`, passed to gdUnit4 as `-i SUITE` (a suite name, a path the
  suite's file contains, or `suite:test`), over a list of the client's tests in the tool and over changing the
  client's tests, because only the caller knows which tests read a project's own wiring, and a measuring tool must not
  change the project it measures. Ignored tests do not run, so a line only they reach reads as not covered; the
  `suite:test` form leaves the suite's other cases running. Asked in the review of #191: without it no instrumented
  run of the client counts.
- 2026-11-12 T4: chose `--timeout` with a process-group kill over waiting on the suite because the first whole-suite
  run hung (§ Measurements): a test's child Godot waited forever, and killing only the runner would have left it
  running on the host.
- 2026-11-12 T4: chose `--exclude PATH` over a built-in list of scripts that tests copy out because the tool cannot
  see which ones a test copies: `tests/ui/kit/kit_reimport_test.gd:26` and `tests/ui/kit/kit_import_test.gd:62`–`63`
  copy `tools/ui/kit_import.gd` into a temporary project with no `KitCov`, where an instrumented copy does not compile.
- 2026-11-12 T4: kept Change step 4's rule, a run counts only on exit 0 or 101, over counting stratics-client's exit
  100, and took the whole-suite numbers from the kept counters (§ Measurements), because the rule is approved and a red
  suite's numbers include the lines of tests that stopped part-way; T7 decides whether a run with failing tests counts.
- 2026-11-12 T2: this record named paths that KIT-042 (#161) and KIT-047 (#177) moved. `docs/maintenance.md:18` is
  now `CONTRIBUTING.md:46` ("the implementing PR closes the issue"); `plugins/dev-core/skills/testing/SKILL.md:23` is
  now `plugins/core/skills/testing/SKILL.md:26`. T2's "INDEX rows in `platforms/tools/INDEX.md` and
  `platforms/ci/validations/INDEX.md`" became the tool's row in `platforms/tools/README.md`, the index of tools;
  `platforms/ci/README.md` lists validations and has no row for a tool's test (`test_complexity.py` and
  `test_gd_duplicates.py` have none).
- 2026-11-12 T5: chose to join a GDScript function to the `gd_coverage.py` report by its repository-relative path and
  `func` line over its name because `gd_spans` keeps the bare `func` name, so two inner classes' functions of one name
  would share a ratio, while both tools start a function at its `func` line. The report writes paths from the
  repository root (`client/app/network/network.gd` in the monorepo), and `complexity.py` takes `FILE` relative to the
  current folder, so it turns each path into one from `git rev-parse --show-toplevel`. A report taken at another
  commit still joins where a function kept its path and line, and the tool says so (notice).
- 2026-11-12 T5: chose to treat an unreadable or foreign `--gd-coverage` file like a missing JaCoCo report (notice,
  CC scores, exit 2 with `--threshold`) over scoring its functions at 0 % coverage, because 0 % turns every CC into
  CC² + CC and would read as a finding that the change did not cause.

## Risks

- [FACT] one-line compound statements and functions get their probe after the colon: `test_gd_coverage.py` `SOURCE`
  holds `if i > 4: break` and `func one(a: int) -> int: return a`, and the instrumented text parses again. The client
  has no one-line compound statement outside `addons/` and `tests/` at `f98e0091` (a `git grep` for `if`, `elif`,
  `else`, `for` or `while` with a body after the colon).
- [FACT] lambdas are not entered: a statement is counted by its first line, so the body lines of a lambda belong to the
  statement that holds it and read as covered when that statement ran, whether or not the lambda was called. 106
  lines in 43 client files hold one.
- [FACT] property `get`/`set` bodies are measured as functions named `<var>.get` and `<var>.set` (`hp` in `SOURCE`);
  class-level `var` initialisers get no probe.
- [FACT] `@tool` scripts get probes like any other: the client's one `@tool` script,
  `features/trade/trade_add_button.gd`, ran instrumented in the whole suite with its 32 statement lines and 4 branch
  outcomes covered and no script error (§ Measurements).
- [FACT] the `.godot` import cache: the copy is instrumented before its one `--import` (§ Decisions). The whole-suite
  run logged the same script errors as a plain copy, line for line, and none names `kit_cov` (§ Measurements).
- [FACT] tests that inspect the project itself see the instrumentation: in stratics-client
  `tests/app/autoload_order_test.gd` finds the `KitCovWriter` autoload and `tests/architecture/dependency_rules_test.gd`
  finds every probed file depending on `kit_cov`, so 3 test cases fail on every instrumented run (§ Measurements). In
  the monorepo client at `ac649c10c`, `tests/ui/size_audit_test.gd` adds 2: its audit quotes source lines into its
  report, and the copy's lines hold the probes (`KitCov.hit(7631); label.autowrap_mode = …`, and a `for` iterable
  wrapped in `KitCov.t`). gdUnit4 6.2.1 skips a test suite or case named with `-i`
  (`src/core/runners/GdUnitTestCIRunner.gd:40`, matched in `is_skipped` at :435), and `--ignore` passes it
  (§ Decisions); the caller names those tests, the tool names none.
- [FACT] `user://` isolation through `HOME` holds on macOS: the real
  `~/Library/Application Support/Godot/app_userdata/Stratics/logs/godot.log` kept mtime 1794305802.564249 across the
  spike, and the runs wrote their logs under the scratch `HOME`.
- [FACT] a `while` loop's entry is not measured, and the operands of `and`/`or` are not separate outcomes: the
  condition probe counts the whole condition.
- [FACT] a script that a test copies into another project runs there without `KitCov` and does not compile. The tool
  cannot see which scripts a test copies; the first whole-suite run hung on one (§ Measurements), and `--exclude`
  leaves it without probes.
- [FACT] tests that start Godot on the copy add their counters to the run's (`hits-<pid>.json`). [HYPOTHESIS] a child
  that its test kills before it exits writes no file, and what it ran reads as uncovered.
- [FACT] gdUnit4 builds a mock from the script's source text: `GdScriptParser.gd` `extract_func_signature` joins the
  rows from the `func` line to the first that ends in `:` (`is_func_end`). A probe never goes on such a row: the first
  probe of a function goes on the row after a multi-line signature, or after the colon of a one-line function, whose
  row already does not end in `:`.
- [FACT] the copy has no sibling folders, so client tests that read the docs repository find it only through
  `STRATICS_DOCS_DIR`: `tests/support/docs_paths.gd` tries the variable, then a parent that holds `game/protocol`,
  then `res://../stratics-docs`. The tool passes the caller's environment to Godot. At `ac649c10c` the monorepo
  client's tests read `game/`, run `platform/tools/content-projection/project.py` and read the LFS mock
  `docs/collab/ui-design-2026-10-11/ui-layout-roadmap.json`, so the folder the variable names needs all three
  (§ Measurements).
- [FACT] `HOME` inside the temporary folder also hides Python's user site-packages from a test that starts `python3`:
  the monorepo client's `tests/content/item_category_test.gd` runs the content projection, whose `jsonschema` import
  failed under the moved `HOME` (run 2 in § Measurements). The caller sets `PYTHONUSERBASE` to the output of
  `python3 -m site --user-base` and the tool passes it on; the tool does not set it itself.
- [FACT] a red suite reports no coverage (Change step 4), and stratics-client `main` is red on its own: a plain copy
  of `310d002a` under Godot 4.7.2 fails every test that mocks `app/network/network.gd`, because gdUnit4 6.2.1 writes
  the multi-line default `OS.has_feature(RELEASE_FEATURE)` of `resolve_server_url` (lines 325–328) into the mock as
  `release_feature` and `os` (§ Measurements). The monorepo client at `ac649c10c` is red on a plain copy as well: 4
  cases of `tests/group/group_menu_invite_test.gd` compare a width such as 158.0 with 157.999969. T7 decides whether a
  run with failing tests counts.
- [FACT] stratics-client `main` stops at `310d002a` ("docs: point readers to the Stratics monorepo (#355)"); the live
  client is `client/` in stratics-docs, where `resolve_server_url` is one line (`client/app/network/network.gd:350` at
  `ac649c10c`). The tool archives `<ref>:client` when it runs inside that folder (`extract`), and a run there counted
  with 9 test cases ignored (§ Measurements).
- [FACT] with coverage, a GDScript function reaches the CRAP target sooner than the old CC-only target: CRAP < 10 fails
  for a fully covered function at CC 10 (CRAP 10.0), which `code-standards`
  (`plugins/core/skills/code-standards/SKILL.md:33`, "CC ≤ 10 (GDScript)") still accepts. 8 of the 62 functions that
  coverage added on the monorepo client are such functions (§ Measurements). The skill text changes with T6, not T5.
- [FACT] a function that only an ignored test reaches reads as not covered and can become a CRAP finding:
  `client/tools/ui/size_audit.gd` `guard` (CC 9) has 0/20 lines covered in the counted run because its one test,
  `test_guard_rejects_new_changed_stale_and_duplicate_entries`, is ignored, and scores CRAP 90.0, the second worst on
  the client (§ Measurements). T7's false-positive count includes such findings.

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

T4 ran the whole stratics-client suite on 2026-11-12 on a `git archive` copy of `310d002a` (stratics-client `main`, see
§ Risks) in a new `mktemp -d` folder under the session's scratchpad; nothing in `stratics-client` was edited. Godot
4.7.2.stable.official.ed1daf0bf and the client's gdUnit4 6.2.1 ran headless under `nice -n 10` with `HOME` inside the
temporary folder. No loop gate run was on the host, but the load average was 10 to 15 throughout (a 4-hour `qa.py soak`
with 100 clients, a Java server and a VM), so the times are upper bounds.

| Run | Result |
|---|---|
| 1, `--ref 310d002a` | hung at about 13:26 in `tests/ui/kit/kit_reimport_test.gd` `test_clean_checkout_extracts_pinned_delivery_and_reuses_it`, whose child Godot runs an instrumented `tools/ui/kit_import.gd` in a project with no `KitCov`; stopped by hand at about 13:30. `--timeout` and `--exclude` come from it (§ Decisions) |
| 2, with `--exclude tools/ui/kit_import.gd` | 577 s, exit 2 ("the suite exited 100"): 2,749 test cases, 610 errors, 696 failures, from two causes that a plain copy shares: the mock failure below and the tests that read the docs repository, which the copy has no sibling of |
| 3, the same with `STRATICS_DOCS_DIR` | 483 s, exit 2 ("the suite exited 100"); the variable named a scratch folder with the `game/protocol` and `game/content/packs/pilot` of stratics-docs `2eb46d4c4`, its last commit before `310d002a` (2026-10-29 16:29) |

Run 3 against a plain copy of the same commit, imported beforehand in 24.78 s and run with the same variable:

| Measure | Plain copy | Instrumented copy (run 3) |
|---|---|---|
| wall time | 388 s, the test run only | 483 s, with archive, LFS fill, instrumentation and `--import` |
| gdUnit4 "Total execution time" | 6 min 6 s 94 ms | 6 min 54 s 236 ms (+13 %, one run each) |
| Overall Summary | 2,749 test cases, 269 errors, 12 failures, 1 skipped, 2 orphans; 375/375 suites | 2,749 test cases, 269 errors, 15 failures, 1 skipped, 2 orphans; 375/375 suites |
| exit | 100 | gdUnit4 100; the tool 2 |
| failing test cases (`results.xml`) | 68 | the same 68, plus 3 |
| script error lines | 172 distinct lines, mock file numbers normalised | the same 172 lines; none names `kit_cov` |

Instrumentation: 250 files got probes in 14,174 counter slots (`SIZE` in the copy's `kit_cov/kit_cov.gd`); no file was
left without probes for a parse error and no LFS object was missing (neither notice was printed). 7 counter files were
written, all with `"reason": "exit_tree"`: the run's own (12,241 non-zero slots) and 6 from the Godot processes that
tests started in the copy.

The 68 shared failures are the client's own: every test that mocks `app/network/network.gd` fails with `Parse Error:
Identifier "release_feature" not declared` and `Identifier "os" not declared` at line 156 of the generated mock, 230
such lines in each log (§ Risks). The 3 failures only the instrumented copy has are tests that inspect the project
itself:

- `tests/app/autoload_order_test.gd:15` `test_autoloads_keep_names_order_and_singleton_flag` expects the 6 autoloads
  and finds `KitCovWriter` in front of them;
- `tests/app/autoload_order_test.gd:28` `test_every_autoload_script_exists` expects 6 autoloads and finds 7;
- `tests/architecture/dependency_rules_test.gd:66` `test_runtime_dependencies_obey_the_module_table` lists every probed
  file as a forbidden dependency on `kit_cov`.

So T4's "no instrumentation failure" holds for the scripts (no parse, compile or runtime error from a probe, the
`@tool` script included) and not for the suite: those 3 cases fail on every instrumented run of this client (§ Risks).

The tool reports nothing for a red suite (Change step 4), so the coverage below comes from the kept run (`--keep`)
through a scratch script that loads `gd_coverage.py`, instruments a new `git archive` of `310d002a` with the same
`--exclude` (the same 14,174 slots) and sums the 7 counter files as `read_hits` does (23.83 s). It includes the lines
that the 71 failing test cases ran before they failed.

| Measure | Result |
|---|---|
| functions | 2,872 in 250 files; 243 files with a covered line |
| statement lines | 20,918/22,997 (91.0 %) |
| branch outcomes | 7,076/8,584 (82.4 %) |
| per function | 2,181 fully covered, 142 with no covered line |
| `app/update/pack_choice.gd` | 46/54 lines and 32/40 outcomes, function by function the same as T1's table |

The monorepo client ran on 2026-11-12 with the tool started in `client/` of a stratics-docs checkout and `--ref
ac649c10c` (the checkout was only read), each run in a new `mktemp -d` folder under the session's scratchpad: Godot
4.7.2.stable.official.ed1daf0bf and the client's gdUnit4 6.2.1 headless under `nice -n 10`, `--exclude
tools/ui/kit_import.gd`, and `STRATICS_DOCS_DIR` at a scratch folder extracted from the same commit. Before each Godot
run `pgrep` found no `loop.py` and no other Godot. The load average was 4.33 when the counted run started and 9.35 when
it ended, from other sessions' work, so its times are upper bounds.

| Run | Docs folder | Ignored | Result |
|---|---|---|---|
| plain copy, imported beforehand | `game/` | none | 444 s, the test run only; gdUnit4 exit 100: 3,524 test cases, 9 failures in 7 cases, 1 skipped, 461/461 suites; "Total execution time" 7 min 10 s 574 ms |
| 1 | `game/` | the 3 autoload and dependency cases | 502 s, exit 2 ("the suite exited 100"): 3,521 test cases, 10 failures in 8 cases (the plain copy's 7 and one `size_audit_test.gd` case); 7 min 40 s 353 ms, +6.9 % on the plain copy |
| 2 | `game/`, the content projection and the UI mock | the 9 below | 530 s, exit 2: 3,515 test cases, 4 failures, all in `item_category_test.gd` (`HOME` hid `jsonschema`, § Risks); 8 min 6 s 823 ms |
| 3, counted | the same, with `PYTHONUSERBASE` | the same 9 | 596 s, exit 0: 3,515 test cases, 0 errors, 0 failures, 1 skipped; 9 min 4 s 57 ms |

The plain copy's 7 failing cases are the client's or the docs folder's, not the tool's: the 4
`group_menu_invite_test.gd` cases compare floats (§ Risks); the 2 `item_category_test.gd` cases and
`size_audit_test.gd` `test_committed_report_is_reproducible_and_covers_every_role` read the content projection and
the UI mock, which that docs folder lacked ("the mock reference cannot be read"). Run 3 ignores 9 cases, by
`suite:test`, so the rest of each suite runs:

- the 3 cases above that see the `KitCovWriter` autoload and the `kit_cov` dependency;
- `size_audit_test.gd` `test_guard_rejects_new_changed_stale_and_duplicate_entries` and
  `test_committed_report_is_reproducible_and_covers_every_role`, whose audit quotes the probed source (§ Risks);
- the 4 `group_menu_invite_test.gd` cases that fail on the plain copy too, because a run with failing tests does not
  count until T7.

The 3 runs' times are not an overhead measure: they ran at different loads, and gdUnit4's test time grew from run 1 to
run 3 with fewer cases. The one paired measure is the plain copy against run 1, +6.9 %.

| Measure | Run 3 |
|---|---|
| functions | 3,280 in 276 of the 283 instrumented files (`tools/ui/kit_import.gd` excluded) |
| statement lines | 24,766/26,685 (92.8 %) |
| branch outcomes | 8,310/9,860 (84.3 %) |
| per function | 2,393 fully covered, 116 with no covered line |
| probes | 6,463 `hit`, 4,712 `b` and 559 `t` in 16,446 counter slots; 37 lines unmeasured |
| counter files | the run's own and 6 from the Godot processes that tests started in the copy |
| tool timings | instrumentation 11.3 s, `--import` 21.7 s, suite 559.1 s; 4,565 LFS pointers filled, 0 missing |

T5 ran on 2026-11-12 with run 3's report and gdtoolkit 4.5.0, on a new Git repository holding only the 1,047
`client/**/*.gd` files of `ac649c10c`, so its root matches the report's paths (the stratics-docs checkout was only
read); the 276 files of the report were the `FILE` arguments, and each run took about 6 s. gdradon cannot parse 3 of
them (`client/features/battle/battle.gd` line 704, `client/features/mail/mail_window.gd` line 222 and
`client/features/world/movement/remote_track.gd` line 13, "invalid syntax"), so their functions are not measured with
or without coverage.

| `complexity.py` run | Result |
|---|---|
| without `--gd-coverage` (KIT-031) | 66 of 3,114 measured functions above target, all by CC |
| `--gd-coverage` run 3's report | "GDScript coverage for 3114 of 3114 measured function(s)"; 128 of 3,114 above target, all by CRAP; the notice names the report's ref `ac649c10c070` against the copy's HEAD `2072376d2326`, and every function joined because the files are the same |

The 66 CC findings all stay, as CRAP is never below CC; 32 of them are fully covered, so their CRAP equals their CC.
Of the 62 that coverage adds, 26 are at CC 10 (8 fully covered, CRAP 10.0, § Risks) and 36 at CC 3 to 9 with lines not
covered (CC derived from CRAP and the report's line ratio). The worst three are `client/app/network/network.gd`
`_validate_message` (CC 224, 299/320 lines) at CRAP 238.2, `client/tools/ui/size_audit.gd` `guard` (0/20 lines; its
test is ignored, § Risks) at 90.0 and `client/tools/ui/build_shop_theme.gd` `_build_hair` (0/30 lines) at 72.0.

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

T2–T4: run from the worktree root at `1b9f3ba` on 2026-11-12, rebased on `38a760b` (the commits after it change only
this document); every command exited 0:

- `bash platforms/tools/check.sh` and `CI=1 bash platforms/tools/check.sh`: "check: OK (1 plugins, 27 skills, 4 rules,
  11 templates, 14 readmes, 82 links, 25 hook cases)", then "✔ Validation passed" twice and no skip line.
- `bash platforms/tools/smoke.sh`: "smoke: OK (27 skills, app fallback, cleanup, symlink safety, manifests,
  sync-project, rules copy, vendored skills, multi-profile sync, no-spec repo)".
- `python3 platforms/ci/validations/check_kit.py --links`: the same "check: OK" line.
- `python3 -B -m unittest discover -s platforms/ci/validations -p "test_*.py"`: "Ran 143 tests in 128.834s", "OK
  (skipped=4)"; 3 of the 4 skips are `test_gd_coverage.py` `GodotTest`, which needs `KIT_GDUNIT4`.
- `KIT_GDUNIT4=<a gdUnit4 6.2.1 addons/gdUnit4 folder> nice -n 10 python3 -B -m unittest test_gd_coverage` in
  `platforms/ci/validations`, with Godot 4.7.2 and gdtoolkit 4.5.0: "Ran 21 tests in 44.089s", "OK", no skip. It ran
  before the rebase, which changed neither the tool nor its tests.
- `python3 platforms/tools/gen_index.py --check`: "gen_index: plugin indexes are current".
- `bash platforms/tools/vendor.sh --check`: "vendor: lock consistent".
- `claude plugin validate plugins/core`: "✔ Validation passed".
- `gitleaks git --redact --log-opts="origin/main..HEAD"`: "1 commits scanned.", "scanned ~76406 bytes (76.41 KB) in
  77ms", "no leaks found".
- `git merge-tree --write-tree HEAD origin/main` against `3834729` (KIT-054, #190): no conflict.

`--ignore` and the monorepo run: run from the worktree root at `2815bd6` on 2026-11-12 (the commit after it changes
only this document); every command exited 0:

- `bash platforms/tools/check.sh` and `CI=1 bash platforms/tools/check.sh`: "check: OK (1 plugins, 27 skills, 4 rules,
  11 templates, 14 readmes, 83 links, 25 hook cases)", then "✔ Validation passed" twice and no skip line.
- `bash platforms/tools/smoke.sh`: "smoke: OK (27 skills, app fallback, cleanup, symlink safety, manifests,
  sync-project, rules copy, vendored skills, multi-profile sync, no-spec repo)".
- `python3 platforms/ci/validations/check_kit.py --links`: the same "check: OK" line.
- `python3 -B -m unittest discover -s platforms/ci/validations -p "test_*.py"`: "Ran 146 tests in 117.315s", "OK
  (skipped=5)"; 4 of the 5 skips are `test_gd_coverage.py` `GodotTest`, which needs `KIT_GDUNIT4`.
- `env KIT_GDUNIT4=<a gdUnit4 6.2.1 addons/gdUnit4 folder> nice -n 10 python3 -B -m unittest -v test_gd_coverage` in
  `platforms/ci/validations`, with Godot 4.7.2 and gdtoolkit 4.5.0: "Ran 23 tests in 29.853s", "OK", no skip.
- `python3 platforms/tools/gen_index.py --check`: "gen_index: plugin indexes are current".
- `bash platforms/tools/vendor.sh --check`: "vendor: lock consistent".
- `claude plugin validate plugins/core`: "✔ Validation passed".
- `gitleaks git --redact --log-opts="origin/main..HEAD"`: "1 commits scanned.", "scanned ~11867 bytes (11.87 KB) in
  39.1ms", "no leaks found".
- `git merge-tree --write-tree HEAD origin/main` against `86a4564` (#191): no conflict.

## History

- 2026-11-10: confirmed (owner, ub-mode evaluation decisions D3 and D5).
- 2026-11-11: implementation prompt launched; issue #136; T1 spike run.
- 2026-11-11: specification and T1 spike in #144, which refers to #136 and leaves it open.
- 2026-11-12: the owner approved T2 onward in chat ("Sim, KIT-034 primeiro"), and KIT-035 after T4 is merged;
  T2–T4 implemented and the whole client suite measured in #191, which refers to #136 and leaves it open.
- 2026-11-12: `--ignore` and a counted run on the monorepo `client/` in #193, which refers to #136 and leaves it
  open.
