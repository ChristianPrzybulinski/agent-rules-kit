---
id: KIT-035
title: "Advisory GDScript mutation testing of changed, covered functions, with PIT's default operators"
status: confirmed
confirmed: "2026-11-10 (owner, ub-mode evaluation decisions D3 and D5 in the chat of the ub-mode evaluation session; implementation prompt launched 2026-11-11)"
issue: "#137"
pr: ""
---

# KIT-035 — Advisory GDScript mutation testing of changed, covered functions, with PIT's default operators

## Problem and evidence

The owner evaluated the ub-mode principles against the kit on 2026-11-10
(`/Users/christian/Developer/GitHub/PROPOSAL-UB-MODE-2026-11-10.md`, row 29 at line 103, the parity rows and build
order at lines 127–133 and § 5 "KIT-034 — GDScript mutation (ours)" at lines 270–280, which this feature implements
under its real id). The kit builds its own GDScript tools (D3) and gives GDScript every check Java has (D5). This PR
holds the feature docs and the measured T1 spike only; the owner decides on T2 and later from the T1 numbers. Facts
re-checked at kit `49b2137`, stratics-client `f98e0091` and stratics-server `5bce89c2`:

- [FACT] the same rule has a mutation gate in Java and none in GDScript.
  `plugins/dev-core/skills/testing/SKILL.md:19` asks domain rules for "mutation score ≥80%"; line 23: "GDScript
  (Godot): no line, branch or mutation percentage gate; the tooling does not exist."
  `plugins/dev-java/skills/java-standards/references/build-and-dependencies.md:36`: "| `pitest-maven` | mutation
  testing | ≥80% in `domain` |".
- [FACT] the test runner has no mutation support: `grep -rli mutat addons/gdUnit4` in the client matches no file.
- [FACT] the server pins PIT and names no operator: `stratics-server/pom.xml:138` pins `pitest-maven` 1.30.0 (with
  `pitest-junit5-plugin` 1.2.3 at line 266 and `junit-platform-launcher` 6.0.2 at line 273); its configuration
  (lines 276–295) sets `mutationThreshold` 80 (line 291) and `failWhenNoMutations` true (line 294) and has no
  `<mutators>`.
- [FACT] with no operator named, PIT 1.30.0 runs its unnamed default set: in
  `~/.m2/repository/org/pitest/pitest/1.30.0/pitest-1.30.0.jar`, `javap -c -p` shows
  `org.pitest.mutationtest.engine.gregor.config.GregorEngineFactory` calling `Mutator.newDefaults()` when the list
  is empty, and `newDefaults()` returning `INVERT_NEGS`, `MATH`, `VOID_METHOD_CALLS`, `NEGATE_CONDITIONALS`,
  `CONDITIONALS_BOUNDARY` and `INCREMENTS` plus `betterReturns()`: `TRUE_RETURNS`, `FALSE_RETURNS`,
  `PRIMITIVE_RETURNS`, `EMPTY_RETURNS` and `NULL_RETURNS`. That is the prompt's list. The named group `DEFAULTS`
  (`StandardMutatorGroups`) differs: it holds `REMOVE_CONDITIONALS_ORDER_ELSE` and `REMOVE_CONDITIONALS_EQUAL_ELSE`
  in place of `NEGATE_CONDITIONALS`, and it applies only when a pom names it.
- [FACT] the cost was unknown: the proposal's row 29 (line 103) says "one headless Godot run per mutant [HYPOTHESIS
  until the KIT-034 spike measures it]", and lines 303–304 "mutation needs one headless Godot run per mutant; the T1
  spikes measure both before any further work".
- [FACT] mutating only covered lines needs KIT-034 (#136), the GDScript coverage tool this feature reads.

## Change

T1 (#145) added this file, its row in `docs/features/README.md` and one CHANGELOG line. T2–T4 add
`platforms/tools/gd_mutation.py`, `platforms/ci/validations/test_gd_mutation.py`, the tool's row in
`platforms/tools/README.md` and one CHANGELOG line. T5 changes the same tool, its test and its row and adds one
CHANGELOG line. No skill or gate changes before T7.

The tool, `platforms/tools/gd_mutation.py` (Python 3.9+, gdtoolkit 4.5.0, our own code, D3); steps 1–5 and 8 are
built in T2–T4, the cache (6) is T5 and the load-bounded workers (7) are T6 (T3 has `--workers N`, default 1):

1. **Operators**, one per PIT default operator, placed from the gdtoolkit tree (line and column), each mutant one text
   edit that keeps every line number:

   | PIT 1.30.0 operator | GDScript mutant |
   |---|---|
   | `CONDITIONALS_BOUNDARY` | `<` ↔ `<=`, `>` ↔ `>=` |
   | `NEGATE_CONDITIONALS` | `==` ↔ `!=`, `<` → `>=`, `<=` → `>`, `>` → `<=`, `>=` → `<`, `in` ↔ `not in`, `is` ↔ `is not`; `not` or `!` removed, or `not (…)` added around a bare condition, as in `if not x:` ↔ `if x:` |
   | `MATH` | `+` ↔ `-`, `*` ↔ `/`, `%` → `*`, `&` ↔ `\|`, `^` → `&`, `<<` ↔ `>>` |
   | `INCREMENTS` | `+=` ↔ `-=` |
   | `INVERT_NEGS` | `-x` → `x`, not on a number |
   | `VOID_METHOD_CALLS` | a call standing alone as a statement → `pass`, not on `print*`, `push_error`, `push_warning` or `assert` |
   | `TRUE_RETURNS`, `FALSE_RETURNS` | the returned expression → `true` or `false` in a `-> bool` function |
   | `PRIMITIVE_RETURNS` | → `0` or `0.0` in a `-> int` or `-> float` function |
   | `EMPTY_RETURNS` | → `""`, `&""`, `[]`, `{}` or an empty `Packed*Array` for those return types |
   | `NULL_RETURNS` | → `null` in a function returning a class, `Variant` or nothing typed |

   A mutant the return type cannot hold (`null` in `-> String`), or equal to the value already returned, is not
   generated.
2. **Scope.** Only the functions whose lines changed (`--base REF`, read as `complexity.py` reads them) and only the
   lines KIT-034 reports covered; a mutant on an uncovered line is listed as "no coverage" without a run.
3. **Copy.** One `git archive` copy in `mktemp -d`, imported once (`godot --path <copy> --headless --import`); each
   worker works on its own APFS clone (`cp -cR`). A mutant is written into the worker's file, run and restored.
4. **Tests.** The test files under `tests/` that name the mutated file's `class_name` or its `res://` path, run with the
   project's own gdUnit4 command (`stratics-client/tools/dev.sh:42`, one `-a` per file). The timeout is 10 × the
   baseline time of the same selection plus 30 s (`--timeout-constant`).
5. **Status.** Per mutant, from the exit code and the log: *killed* (exit 100), *survived* (exit 0 or 101 with an
   "Overall Summary" of one test case or more), *timed out*, *invalid* (the mutant does not load: exit 105, or a parse
   or compile error before the tests run) and *error* (anything else); *not run*, with exit 2, when writing or running
   the mutant raises. The score is killed plus timed out over killed, timed out and survived; invalid mutants stay out
   of it.
6. **Differential.** Each mutant's result is cached under a hash of its function's path, name and text (line ends
   and trailing blanks aside) together with the `res://` path and content hash of each selected test file, and its
   place in the function, so a function whose hash did not change keeps its last result (ub-mode's idea) on whatever
   lines it moves to, a new or changed test makes it run again, and a second run with nothing changed starts no
   Godot. `--cache FILE` moves the cache and `--no-cache` runs every mutant.
7. **Workers.** Parallel workers, each starting a mutant only while the one-minute load average is below the core
   count and fewer than 2 gate runs hold the host (the loop's gates count).
8. **Output.** One survivor per line on stdout, `path:line function OPERATOR from → to`, then a summary with the score
   on stderr. Exit 0 (advisory); a gate waits for T8.

`plugins/dev-core/skills/testing/SKILL.md:23` and `testable-game-logic.md:28` change only in T7, after the tool exists.
No CI or loop gate runs it (D2, D5).

## Tasks

| Task | What | Done when |
|---|---|---|
| T1 | Spike: hand-picked mutants of `PackChoice.check` (`app/update/pack_choice.gd:11`–`58`) against `tests/update/pack_choice_test.gd`; time per mutant and kill rate | the numbers are in § Measurements (this PR) |
| T2 | Operators on the gdtoolkit tree and `platforms/ci/validations/test_gd_mutation.py` (parser cases `skipUnless` gdtoolkit): each operator's mutant parses again and keeps line numbers; no mutant the return type cannot hold | tests green; the tool's row in `platforms/tools/README.md` (§ Decisions, 2026-11-12 T2) |
| T3 | Runner: copy, clone per worker, related tests, baseline, timeout, status, restore | a run on one client file matches T1's statuses |
| T4 | Changed functions and covered lines from KIT-034 T4's JSON; "no coverage" without a run | needs KIT-034 T4 merged |
| T5 | Differential cache by function and test hashes | a second run with nothing changed starts no Godot |
| T6 | Workers bounded by load and the gate cap | measured on the client with the loop running |
| T7 | `testing` § GDScript and `testable-game-logic.md:28` name the advisory command; one eval case that does not name its skill; descriptions unchanged | `check.sh`, the eval and the skill size caps pass |
| T8 | Time and false survivors (equivalent mutants) over two loop batches; the owner decides on a gate (proposal line 284) | numbers in § Measurements and an owner decision |

The PR of the last task the owner approves closes #137; this PR refers to it.

## Decisions

- 2026-11-11 T1 (#145): chose PIT's unnamed default set (`Mutator.newDefaults()`) over the named group `DEFAULTS`
  because `stratics-server/pom.xml` names no `<mutators>` (lines 276–295), so `newDefaults()` is what the Java gate
  runs.
- 2026-11-11 T1 (#145): chose hand-picked text edits over a generator for T1 because the spike measures the cost and
  the kill rate of a run, and T2 builds the operators on the gdtoolkit tree.
- 2026-11-11 T1 (#145): chose a hash of the function together with its selected test files over the function hash
  alone because a new or changed test can kill a survivor whose function did not change.
- 2026-11-11 T1 (#145): chose to keep invalid mutants out of the score over counting them as killed because a mutant
  that does not load says nothing about the tests: M10 (`return null` in a `-> String` function) exits 105 with
  "Script errors were detected during test discovery!" before any test runs, so T2 does not generate it.
- 2026-11-11 T1 (#145): chose "Refs #137" over "Closes #137" because `docs/maintenance.md:18` says "the implementing
  PR closes the issue" and this PR implements T1 only.

- 2026-11-12 T2: this record named paths that KIT-042 (#161) and KIT-047 (#177) moved, as KIT-034 noted.
  `docs/maintenance.md:18` is now `CONTRIBUTING.md:46` ("the implementing PR closes the issue");
  `plugins/dev-core/skills/testing/SKILL.md:23` is now `plugins/core/skills/testing/SKILL.md:26`. T2's "INDEX rows in
  `platforms/tools/INDEX.md` and `platforms/ci/validations/INDEX.md`" became the tool's row in
  `platforms/tools/README.md`, the index of tools; `platforms/ci/README.md` lists validations and has no row for a
  tool's test.
- 2026-11-12 T2: chose to import `gd_coverage.py`'s helpers (`extract`, `find_project`, `run_godot`, `scratch_env`,
  `parse_errors`, `test_summary`, the parser and the counted exits) and `complexity.changed_lines` over copying them,
  because the copy, the scratch `HOME`, the process-group kill and the gdUnit4 command must stay the ones KIT-034
  measured; `gd_coverage.py` is not changed.
- 2026-11-12 T2: chose to emit mutants in tree order, a node before its children, over sorting them by line, because
  a return mutant then comes before a `MATH` mutant inside the returned expression and the JSON reads as the source
  does; stdout sorts the survivors by path, line, column and operator.
- 2026-11-12 T2: chose to add `not (C)` only around the condition of an `if`, `elif`, `while`, match guard or ternary,
  or around an operand of its `and`/`or`, that is not already a comparison or a `not`, `in` or `is` test, over every
  boolean expression, because those already get `NEGATE_CONDITIONALS` from their operator and PIT negates jumps, not
  values.
- 2026-11-12 T2: chose to read the return type from the declaration (`-> T`, a getter's variable type) and skip a
  return mutant the type cannot hold, and one equal to the value already returned, over generating it and counting it
  invalid, because T1's M10 (`null` in `-> String`) exits 105 before any test runs and costs a Godot run for nothing;
  `null` goes only to no type, `Variant` or a class, never a value type or an enum.
- 2026-11-12 T3: chose to put the copy in `tempfile.mkdtemp()` (so `TMPDIR` picks the folder) and remove it at the
  end unless `--keep`, over a fixed folder, because two runs on one host must not share a copy.
- 2026-11-12 T3: chose one unmutated run per test selection that must exit 0 or 101 with one test case or more, as
  `gd_coverage.py` counts a run, over trusting the selection, because a red or empty baseline would mark every mutant
  survived or killed for the wrong reason; its mutants are then "not run" and the tool exits 2.
- 2026-11-12 T3: chose "invalid" for exit 105 or a parse or compile error that names the mutated file's `res://`
  path, checked before exit 100, over exit 105 alone, because a mutant that breaks a script another suite loads can
  fail the run with a compile error that is not the tests' verdict.
- 2026-11-12 T4: chose to refuse `--base` with a `--ref` other than `HEAD` (exit 2, "--base reads the change of HEAD,
  not of REF") over diffing the other ref, because `complexity.changed_lines` reads `<base>...HEAD`, and the lines of
  one ref placed on another's copy would mutate the wrong statements.
- 2026-11-12 T4: chose to join `--coverage` by statement span (a statement covers line L when its `line` <= L <=
  `end`): a line with a hit runs, a line whose statements all have 0 hits is "no coverage", and a line the report does
  not measure (no statement, or `null` hits) runs and is counted in one notice, over skipping it, because an
  unmeasured line is unknown, not uncovered.
- 2026-11-12 review of #192: chose "not run" and exit 2 for a mutant whose write or run raises (an `OSError` from the
  file write, `Popen` or the log append), with a notice naming the exception, the worker then taking the next mutant,
  over "error" with exit 0, because "error" measures the mutant (Godot ran and ended outside the known exits) while a
  raise is the host's failure, and exit 0 would show the score of a subset as the whole. A worker that cannot restore
  its file stops, since every later mutant in its clone would run against a broken source; the mutants no worker took
  are "not run".
- 2026-11-12 review of #192: chose a mutant timeout of 10 × the selection's unmutated time plus `TIMEOUT_CONSTANT`
  (30 s, `--timeout-constant S`) over 10 × alone, because a run stopped early counts as detected and raises the score.
  It is PIT's shape: PIT 1.30.0 allows `round(time × factor) + constant`, factor 1.25 and constant 4000 ms
  (`PercentAndConstantTimeoutStrategy.DEFAULT_CONSTANT` in `pitest-1.30.0.jar`; the Maven plugin's `timeoutConstant`
  default is 3000 ms in `pitest-maven-1.30.0.jar`'s `plugin.xml`). PIT's constant covers a test in a JVM already
  started; each run here starts Godot, and a start slowed by host load (5–20 on this host during gates) or by
  `--workers N` clones starting together does not grow with the run: at T3's 1.2 s, 10 × alone stops a mutant after
  12 s. 30 s is a judgement, not measured under load; it costs 30 s more per mutant that really hangs (none of T3's
  100). The stub tests pass `--timeout-constant 0`, except the one that checks the default.

- 2026-11-12 T5: chose one cache file at `$XDG_CACHE_HOME/ai-kit/gd-mutation/cache.json` (default `~/.cache`),
  beside `gd_duplicates.py`'s `ai-kit/gd-duplicates`, over a file under `.git` or the checkout, because the key holds
  the function's path from the Git top and its text, not the folder, so clones and worktrees of one repository share
  results, and the tool still writes nothing in the checkout.
- 2026-11-12 T5: chose to keep killed, survived, timed out and invalid only over every status, because those are the
  mutant's verdict against its tests, while error, not run, no coverage and no tests come from the host, the
  unmutated run or that run's coverage report; a mutant that ended in error runs again.
- 2026-11-12 T5: chose to leave Godot's version, the rest of the file and the rest of the project out of the key over
  adding them, because reading Godot's version starts Godot, so a run with nothing changed would start one, and a
  whole-file hash reruns every function of a file when one changes, which is what the cache avoids. A change
  elsewhere that turns a result (a helper, a constant, Godot itself) keeps the old result until the function or a
  selected test changes; `--no-cache` measures again, and `CACHE_VERSION` drops the whole file when an operator or a
  status rule changes.
- 2026-11-12 T5, after #192's review fixes merged in: chose to keep "not run" out of the cache, as "error" is, since a
  write or run that raised says nothing about the mutant, and to leave the timeout out of the key, since it is 10 × a
  baseline measured anew on each run plus `--timeout-constant`, so no key fixes it. A "timed out" kept from a run with a
  lower constant stays until the function or a selected test changes; `--no-cache` measures again.
- 2026-11-12 T5: chose the mutant's place as its line offset in the function, column, replaced length, operator and
  new text over its line number, because a function that moves to other lines (an edit above it) keeps its results;
  the place still names one edit, so a different gdtoolkit cannot give a cached status to another mutant.
- 2026-11-12 T5: chose to keep the 5000 functions used last, merged under an `flock` on `cache.json.lock` and replaced
  whole (`os.replace`), over an unbounded file written in place, because two runs on one host may save at once and a
  cut-off write must not leave half a file; a cache that cannot be read or written prints a notice and every mutant
  runs.

## Measurements

T1 ran in the same driver run as KIT-034 T1 (2026-11-11, 10:11:53 to 10:12:43; Godot 4.7.2.stable.official.ed1daf0bf
headless under `nice -n 10`, `HOME` at a scratch folder), on its own APFS clone (`cp -cR`, 2.38 s) of the imported
`git archive` copy of stratics-client `f98e0091`; nothing in `stratics-client` was edited. Each of ten hand-picked
mutants of `PackChoice.check` (`app/update/pack_choice.gd:11`–`58`) was written into the clone, run against
`tests/update/pack_choice_test.gd` (8 test cases) with the project's own gdUnit4 command, and restored. The two
baseline runs took 0.95 and 0.94 s, so the timeout was 9.5 s.

| Mutant | PIT operator | Line | Edit | Time | Exit | Status |
|---|---|---|---|---|---|---|
| M1 | `NEGATE_CONDITIONALS` | 12 | `if not doc is Dictionary:` → `if doc is Dictionary:` | 0.93 s | 100 | killed: 1 error, 7 failures (runtime error at line 14) |
| M2 | `EMPTY_RETURNS` | 13 | `return "SHAPE"` → `return ""` | 0.94 s | 100 | killed: 1 failure |
| M3 | `NEGATE_CONDITIONALS` | 17 | `!= 1:` → `== 1:` | 1.31 s | 100 | killed: 7 failures |
| M4 | `CONDITIONALS_BOUNDARY` | 36 | `< 1` → `<= 1` | 0.95 s | 0 | **survived**: 8 test cases, 0 failures |
| M5 | `NEGATE_CONDITIONALS` | 36 | `< 1` → `>= 1` | 0.95 s | 100 | killed: 7 failures |
| M6 | `NEGATE_CONDITIONALS` | 48 | `manifest["pck"] != ` → `manifest["pck"] == ` | 0.93 s | 100 | killed: 6 failures |
| M7 | `MATH` | 48 | `+ ".pck"` → `- ".pck"` | 0.95 s | 100 | killed: 6 errors, 4 failures (runtime error at line 48) |
| M8 | `NEGATE_CONDITIONALS` | 53 | `!= 64` → `== 64` | 0.94 s | 100 | killed: 3 failures |
| M9 | `NEGATE_CONDITIONALS` | 56 | `== client_protocol` → `!= client_protocol` | 0.95 s | 100 | killed: 3 failures |
| M10 | `NULL_RETURNS` | 58 | `return "PROTOCOL"` → `return null` | 0.81 s | 105 | **invalid**: `Parse Error: Cannot return a value of type "null" as "String".` at line 58; the test script did not compile |

- Time per mutant: 0.81 to 1.31 s, mean 0.966 s, median 0.945 s; 9.66 s for the ten. Each mutant is one Godot run of
  the selected tests and needs no new `--import`: the clone kept the `.godot` cache, and the mutated text loaded
  (M7's runtime error and M10's parse error name the mutated lines).
- Kill rate: 8 of the 9 valid mutants, 88.9 %. M10 is invalid and stays out of the score; no mutant timed out.
- M4 is a real gap, not an equivalent mutant: the condition at lines 33–37 refuses a `pck_size` below 1, so the
  original accepts 1 and the mutant refuses it, and the test file uses 123456, 0, 123456.0, 9 and 10, never 1. The
  test is not added here, since nothing in the client is edited.
- The restored file ran 8 test cases with 0 failures (0.93 s) after the ten mutants.
- A mutant's cost is one run of its selected tests; this selection is one small file, so the time per mutant of a
  larger selection is its own baseline, which T3 measures.

T3 (2026-11-12, 15:00 to 15:03): `gd_mutation.py --ref ac649c10c --json <scratch>/t3.json app/update/pack_choice.gd`,
run from `client/` of a stratics-docs clone at `ac649c10c` (stratics-docs `origin/main`, the monorepo that holds the
client since stratics-client froze), with `TMPDIR` at a new `mktemp -d` scratch folder; Godot
4.7.2.stable.official.ed1daf0bf headless under `nice -n 10`, `HOME` in the folder, one worker. The tool read only Git
objects: `git status --short` of the clone was empty after the run and the scratch folder was empty (the copy
removed). One other Godot run held the
host (KIT-034's), load average 5–6, no loop gate.

- Selection: only `tests/update/pack_choice_test.gd` names `PackChoice` or `res://app/update/pack_choice.gd` at
  `ac649c10c`, so the tool picked T1's test file by itself. Its unmutated run: exit 0, 16 test cases (8 at T1's
  commit), 1.23 s, so the timeout was 12.33 s.
- Time: 156.65 s wall for the run: 1.4 s generating, 22.02 s for the one `--import`, 122.2 s for the 100 mutants and
  about 11 s for the archive (4,565 LFS pointers filled, none missing), the clone and the unmutated run. A mutant took
  1.02 to 1.36 s, mean 1.222 s, median 1.24 s, about one unmutated run each, as T1 found.
- Mutants: 100 in six functions (60 `NEGATE_CONDITIONALS`, 22 `EMPTY_RETURNS`, 8 `TRUE_RETURNS`, 4
  `FALSE_RETURNS`, 2 `CONDITIONALS_BOUNDARY`, 2 `MATH`, 2 `VOID_METHOD_CALLS`): 92 killed, 7 survived, 1 invalid, 0
  timed out or error; score 92.9 % (92/99).

T1's mutants against T3's, line for line (T1's lines are stratics-client `f98e0091`, T3's are `ac649c10c`, where
`PackChoice.check` was split into `check`, `_check_chain` and `_check_entry` for manifest format 2):

| T1 | T1 line, edit | T1 status | T3 line, mutant | T3 status |
|---|---|---|---|---|
| M1 | 12, `not doc is Dictionary` → `doc is Dictionary` | killed | 13, the same (`NEGATE_CONDITIONALS`) | killed |
| M2 | 13, `"SHAPE"` → `""` | killed | 14, the same (`EMPTY_RETURNS`) | killed |
| M3 | 17, `!= 1` → `== 1` | killed | 18, `not in [1, 2]` → `in [1, 2]`, the same check after format 2 | killed |
| M4 | 36, `< 1` → `<= 1` | **survived** | 79, the same (`CONDITIONALS_BOUNDARY`) | **survived** |
| M5 | 36, `< 1` → `>= 1` | killed | 79, the same (`NEGATE_CONDITIONALS`) | killed |
| M6 | 48, `!=` → `==` | killed | 84, the same | killed |
| M7 | 48, `+ ".pck"` → `- ".pck"` | killed | 84, the same (`MATH`) | killed |
| M8 | 53, `!= 64` → `== 64` | killed | 89, the same | killed |
| M9 | 56, `== client_protocol` → `!=` | killed | 38, the same | killed |
| M10 | 58, `return "PROTOCOL"` → `return null` | invalid (exit 105) | 40, not generated (`null` in `-> String`); `"PROTOCOL"` → `""` instead | killed |

Every T1 status that T2 still generates comes back the same, and M10, the one T1 mutant the return type cannot hold,
is no longer generated, so T3's done-when holds. Of T3's other mutants:

- The one invalid mutant is `MATH` at line 50, `[manifest["base"]] + patches` → `-`: Godot refuses `-` between two
  arrays before any test runs (exit 105). The generator does not know operand types, so such a mutant costs one run
  and stays out of the score.
- Of the 7 survivors, 3 are test gaps: line 19 (`"SHAPE"` → `""` for a format outside 1 and 2; the tests use formats
  1, 2 and 1.0, never 3), line 64 (`"SHAPE"` → `""` for an entry that is not a Dictionary; every patch the tests
  build is one) and line 79 (M4). 4 are equivalent or out of the tests' reach: line 90 (`!= 64` is unreachable,
  since a signature that passes `_SIGNATURE_PATTERN`, 86 characters, `[AQgw]` and `==`, always decodes to 64 bytes),
  line 107 (`FileAccess.open` failing on a file that exists), line 109 (`file.close()` removed: the `FileAccess`
  closes when freed) and line 124 (a constant pattern that fails to compile). T8 counts such false survivors over
  two loop batches.
- No test was added: nothing in the client is edited here.

T5 (2026-11-12, 15:20 to 15:22): T3's command with `--cache <scratch>/cache.json`, run twice in a row from `client/`
of the same stratics-docs clone at `ac649c10c`, with `GODOT` set to a wrapper that logged each call and then ran Godot
4.7.2.stable.official.ed1daf0bf; `nice -n 10`, `TMPDIR` in a new `mktemp -d` folder (the tool puts Godot's `HOME`
there), one worker. No loop gate and no other Godot run held the host (load average 4.2).

| Run | Godot calls | Wall | Statuses | Score |
|---|---|---|---|---|
| 1, empty cache | 103: `--version`, one `--import`, one unmutated run, 100 mutants | 142 s (1.13 s generating, 18.62 s import, 111.8 s mutants) | 92 killed, 7 survived, 1 invalid | 92.9 % |
| 2, nothing changed | 0 | 5 s (1.29 s generating; the rest is the archive, 4,565 LFS pointers filled) | the same, mutant for mutant, each `"cached": true` | 92.9 % |

- Run 2 printed "100 mutant(s) not run: their result is in the cache … and neither their function nor its tests
  changed"; its stdout (the 7 survivors) is byte for byte run 1's, and its JSON has `"godot": null` and no unmutated
  run. T5's done-when holds.
- The cache held 6 functions and 100 mutants in 9,806 bytes, about 1.6 KB per function, so the 5000-function cap is
  about 8 MB.
- The clone's `git status --short` was empty after both runs, and so was the scratch folder (the copy removed).
- Not run on the client: a change to one function or to the test file, since nothing in the client is edited here.
  `test_gd_mutation.py` covers both with a stub Godot: a moved function keeps its results, a changed one and a changed
  test run again.

## Proof

Run from the worktree root at `6614325` on 2026-11-11 (the commits after it change only this document and
`docs/features/README.md`); every command exited 0:

- `bash platforms/tools/check.sh` and `CI=1 bash platforms/tools/check.sh`: "check: OK (14 plugins, 46 skills, 3 rules,
  22 templates, 23 indexes, 123 links, 25 hook cases)", then "✔ Validation passed" 15 times and no skip line.
- `bash platforms/tools/smoke.sh`: "smoke: OK (46 skills, app fallback, cleanup, symlink safety, manifests,
  sync-project, rules copy, vendored skills, multi-profile sync, no-spec repo)".
- `python3 platforms/ci/validations/check_kit.py --links`: "check: OK (14 plugins, 46 skills, 3 rules, 22 templates, 23
  indexes, 123 links, 25 hook cases)".
- `gitleaks git --redact --log-opts="origin/main..HEAD"`: "1 commits scanned.", "scanned ~13537 bytes (13.54 KB) in
  39.8ms", "no leaks found".

T2–T4: run from the worktree root at `17b60ab` on 2026-11-12, on `86a4564` (`origin/main`; the commits after it change
only this document); every command exited 0:

- `bash platforms/tools/check.sh` and `CI=1 bash platforms/tools/check.sh`: "check: OK (1 plugins, 27 skills, 4 rules,
  11 templates, 14 readmes, 83 links, 25 hook cases)", then "✔ Validation passed" twice and no skip line.
- `bash platforms/tools/smoke.sh`: "smoke: OK (27 skills, app fallback, cleanup, symlink safety, manifests,
  sync-project, rules copy, vendored skills, multi-profile sync, no-spec repo)".
- `python3 platforms/ci/validations/check_kit.py --links`: the same "check: OK" line.
- `python3 -B -m unittest discover -s platforms/ci/validations -p "test_*.py"`: "Ran 166 tests in 188.118s", "OK
  (skipped=4)"; the 22 tests of `test_gd_mutation.py` ran (gdtoolkit 4.5.0 installed), none skipped.
- `python3 platforms/tools/gen_index.py --check`: "gen_index: plugin indexes are current".
- `bash platforms/tools/vendor.sh --check`: "vendor: lock consistent".
- `claude plugin validate plugins/core`: "✔ Validation passed".
- `gitleaks git --redact --log-opts="origin/main..HEAD"`: "1 commits scanned.", "scanned ~71034 bytes (71.03 KB) in
  89ms", "no leaks found".

T2–T4 review fixes: run from the worktree root at `0e0b6a6` on 2026-11-12, on `cd9a632` (`origin/main`, merged in at
`d70b0ef`; the commits after it change only this document); every command exited 0:

- `bash platforms/tools/check.sh` and `CI=1 bash platforms/tools/check.sh`: "check: OK (1 plugins, 27 skills, 4 rules,
  11 templates, 14 readmes, 83 links, 25 hook cases)", then "✔ Validation passed" twice and no skip line.
- `bash platforms/tools/smoke.sh`: "smoke: OK (27 skills, app fallback, cleanup, symlink safety, manifests,
  sync-project, rules copy, vendored skills, multi-profile sync, no-spec repo)".
- `python3 platforms/ci/validations/check_kit.py --links`: the same "check: OK" line.
- `python3 -B -m unittest discover -s platforms/ci/validations -p "test_*.py"`: "Ran 171 tests in 160.227s", "OK
  (skipped=5)"; the 25 tests of `test_gd_mutation.py` ran, none skipped. The fifth skip is the `GodotTest` case #193
  added to `test_gd_coverage.py`, which needs `KIT_GDUNIT4`.
- `python3 platforms/tools/gen_index.py --check`: "gen_index: plugin indexes are current".
- `bash platforms/tools/vendor.sh --check`: "vendor: lock consistent".
- `claude plugin validate plugins/core`: "✔ Validation passed".
- `gitleaks git --redact --log-opts="origin/main..HEAD"`: "3 commits scanned.", "scanned ~84268 bytes (84.27 KB) in
  54.4ms", "no leaks found".
- The three new tests fail on `gd_mutation.py` as of `aafed4a` (a scratch copy, the tests' `--timeout-constant` left
  out): "Ran 25 tests in 29.170s", "FAILED (failures=3)". The two raise tests stop at the exit code, 0 where 2 is
  expected (the raise ended the worker's thread); the timeout test stops at the baseline timeout, 10 × alone.

T5: run from the worktree root at `c164509` on 2026-11-12, on `aafed4a` (#192's head; `origin/main` is `86a4564`);
the commit after it changes only this document; every command exited 0:

- `bash platforms/tools/check.sh` and `CI=1 bash platforms/tools/check.sh`: "check: OK (1 plugins, 27 skills, 4 rules,
  11 templates, 14 readmes, 83 links, 25 hook cases)", then "✔ Validation passed" twice and no skip line.
- `bash platforms/tools/smoke.sh`: "smoke: OK (27 skills, app fallback, cleanup, symlink safety, manifests,
  sync-project, rules copy, vendored skills, multi-profile sync, no-spec repo)".
- `python3 platforms/ci/validations/check_kit.py --links`: the same "check: OK" line.
- `python3 -B -m unittest discover -s platforms/ci/validations -p "test_*.py"`: "Ran 173 tests in 218.017s", "OK
  (skipped=4)"; the 29 tests of `test_gd_mutation.py` ran (gdtoolkit 4.5.0 installed), none skipped.
- `python3 platforms/tools/gen_index.py --check`: "gen_index: plugin indexes are current".
- `bash platforms/tools/vendor.sh --check`: "vendor: lock consistent".
- `claude plugin validate plugins/core`: "✔ Validation passed".
- `gitleaks git --redact --log-opts="origin/main..HEAD"`: "3 commits scanned.", "scanned ~93707 bytes (93.71 KB) in
  87ms", "no leaks found".

## History

- 2026-11-10: confirmed (owner, ub-mode evaluation decisions D3 and D5).
- 2026-11-11: implementation prompt launched; issue #137; T1 spike run.
- 2026-11-11: specification and T1 spike in #145, which refers to #137 and leaves it open.
- 2026-11-12: the owner approved T2 onward of KIT-034 and KIT-035 in chat ("Sim, KIT-034 primeiro"), KIT-035 after
  KIT-034 T4 merged (`86a4564`, #191); T2–T4 implemented and T3 measured against T1 in #192, which refers to #137
  and leaves it open.
- 2026-11-12: T5 (the differential cache) implemented and measured on the client in its own PR, stacked on #192, which
  refers to #137 and leaves it open.
- 2026-11-12: the review of #192 asked for `main` merged in (`cd9a632`, #193; the tools README rows of both kept), a
  status for a mutant whose run raises and a floor under the mutant timeout; both are in § Decisions.
