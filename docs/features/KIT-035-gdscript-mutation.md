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

This PR adds this file, its row in `docs/features/README.md` and one CHANGELOG line. No tool, skill or gate changes
until the owner approves T2.

The tool it specifies, `platforms/tools/gd_mutation.py` (Python 3.9+, gdtoolkit 4.5.0, our own code, D3):

1. **Operators**, one per PIT default operator, placed from the gdtoolkit tree (line and column), each mutant one text
   edit that keeps every line number:

   | PIT 1.30.0 operator | GDScript mutant |
   |---|---|
   | `CONDITIONALS_BOUNDARY` | `<` ↔ `<=`, `>` ↔ `>=` |
   | `NEGATE_CONDITIONALS` | `==` ↔ `!=`, `<` → `>=`, `<=` → `>`, `>` → `<=`, `>=` → `<`; `not` removed, or added around a bare condition, as in `if not x:` ↔ `if x:` |
   | `MATH` | `+` ↔ `-`, `*` ↔ `/`, `%` → `*`, `&` ↔ `\|`, `^` → `&`, `<<` ↔ `>>` |
   | `INCREMENTS` | `+=` ↔ `-=` |
   | `INVERT_NEGS` | `-x` → `x` |
   | `VOID_METHOD_CALLS` | a call standing alone as a statement → `pass` |
   | `TRUE_RETURNS`, `FALSE_RETURNS` | the returned expression → `true` or `false` in a `-> bool` function |
   | `PRIMITIVE_RETURNS` | → `0` in a `-> int` or `-> float` function |
   | `EMPTY_RETURNS` | → `""`, `[]`, `{}` or an empty `Packed*Array` for those return types |
   | `NULL_RETURNS` | → `null` in a function returning an Object type or nothing typed |

   A mutant the return type cannot hold (`null` in `-> String`) is not generated.
2. **Scope.** Only the functions whose lines changed (`--base REF`, read as `complexity.py` reads them) and only the
   lines KIT-034 reports covered; a mutant on an uncovered line is listed as "no coverage" without a run.
3. **Copy.** One `git archive` copy in `mktemp -d`, imported once (`godot --path <copy> --headless --import`); each
   worker works on its own APFS clone (`cp -cR`). A mutant is written into the worker's file, run and restored.
4. **Tests.** The test files under `tests/` that name the mutated file's `class_name` or its `res://` path, run with the
   project's own gdUnit4 command (`stratics-client/tools/dev.sh:42`, one `-a` per file). The timeout is 10 × the
   baseline time of the same selection.
5. **Status.** Per mutant, from the exit code and the log: *killed* (exit 100), *survived* (exit 0 or 101 with an
   "Overall Summary" of one test case or more), *timed out*, *invalid* (the mutant does not load: exit 105, or a parse
   or compile error before the tests run) and *error* (anything else). The score is killed plus timed out over killed,
   timed out and survived; invalid mutants stay out of it.
6. **Differential.** Each function's result is cached by a hash of its normalised text together with the hashes of
   its selected test files, so a function whose hash did not change keeps its last result (ub-mode's idea), and a new
   test makes it run again.
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
| T2 | Operators on the gdtoolkit tree and `platforms/ci/validations/test_gd_mutation.py` (parser cases `skipUnless` gdtoolkit): each operator's mutant parses again and keeps line numbers; no mutant the return type cannot hold | tests green; INDEX rows in `platforms/tools/INDEX.md` and `platforms/ci/validations/INDEX.md` |
| T3 | Runner: copy, clone per worker, related tests, baseline, timeout, status, restore | a run on one client file matches T1's statuses |
| T4 | Changed functions and covered lines from KIT-034 T4's JSON; "no coverage" without a run | needs KIT-034 T4 merged |
| T5 | Differential cache by function and test hashes | a second run with nothing changed starts no Godot |
| T6 | Workers bounded by load and the gate cap | measured on the client with the loop running |
| T7 | `testing` § GDScript and `testable-game-logic.md:28` name the advisory command; one eval case that does not name its skill; descriptions unchanged | `check.sh`, the eval and the skill size caps pass |
| T8 | Time and false survivors (equivalent mutants) over two loop batches; the owner decides on a gate (proposal line 284) | numbers in § Measurements and an owner decision |

The PR of the last task the owner approves closes #137; this PR refers to it.

## Decisions

- 2026-11-11 T1 ({PR}): chose PIT's unnamed default set (`Mutator.newDefaults()`) over the named group `DEFAULTS`
  because `stratics-server/pom.xml` names no `<mutators>` (lines 276–295), so `newDefaults()` is what the Java gate
  runs.
- 2026-11-11 T1 ({PR}): chose hand-picked text edits over a generator for T1 because the spike measures the cost and
  the kill rate of a run, and T2 builds the operators on the gdtoolkit tree.
- 2026-11-11 T1 ({PR}): chose a hash of the function together with its selected test files over the function hash
  alone because a new or changed test can kill a survivor whose function did not change.
- 2026-11-11 T1 ({PR}): chose to keep invalid mutants out of the score over counting them as killed because a mutant
  that does not load says nothing about the tests: M10 (`return null` in a `-> String` function) exits 105 with
  "Script errors were detected during test discovery!" before any test runs, so T2 does not generate it.
- 2026-11-11 T1 ({PR}): chose "Refs #137" over "Closes #137" because `docs/maintenance.md:18` says "the implementing
  PR closes the issue" and this PR implements T1 only.

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

## History

- 2026-11-10: confirmed (owner, ub-mode evaluation decisions D3 and D5).
- 2026-11-11: implementation prompt launched; issue #137; T1 spike run.
