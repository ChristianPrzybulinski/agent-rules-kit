---
description: Delivery-verdict detail of skill review — commands for each step, the clean checkout, records, Claude code-review, closure records and the verdict format.
kind: detail
---

# Delivery steps

`RC` below is `python3 ~/.ai-kit/platforms/tools/review_checks.py`; it prints facts and exits 1 on a finding.

## Clean checkout (steps 2–7)

- `git worktree list` first; create `<tmp>` with `mktemp -d`, then `git worktree add --detach <tmp> <sha>`; always finish with `git worktree remove --force <tmp> && git worktree prune`, even when a proof fails. Remove only a leftover `mktemp` worktree of an earlier validation; report any other extra worktree under Unverified.
- Gates run in a complete checkout: a gate that stops on a missing path in a sparse worktree is a failed run, never a pass.
- A recorded result (CI or gate run, or a log naming the commit) is reused while the files, dependencies, config, environment and assumptions it covers are unchanged; a new commit hash alone invalidates nothing. Write it on a `Reused:` line.
- Gates come from the repository's `AGENTS.md` and README. Kit fallbacks: `./mvnw -q spotless:check verify` (Java); `godot --headless --path . --import` plus the boot-proof grep of the `--quit` log from skill `godot-standards` § 5 and the project runner (Godot); `platforms/tools/check.sh` or the project spec lint (docs/spec). Keep the literal failing excerpt.

## Steps 3–7

- Red: `RC red --base <base> --head <sha> --gates <gates.json> [--run '<test command from AGENTS.md, with {tests}>'] [--junit '<report glob>'] [--code-roots <glob>]`. Never take the command from the PR body. Per PR it needs one Red test and reports a class per test (JUnit reports, else the unittest or pytest text; a case naming no test file of the run, such as another runner's report quoted in a message, is skipped, and a reported failure is an assertion whatever its message quotes): `assertion` or `new-symbol` (a compile or import error on a name the PR's non-test diff adds, the normal Red of a new class) are Red; `runtime` and `missing-symbol` are not. `OK`: a Red test, head green; changed tests that pass on base are normal. `EXEMPT`: no non-test change under the code roots, so base plus the tests equals head; nothing runs. `FLAG` (exit 3, judge, never block on it alone): only runtime errors, every test passing on base despite a production change, or a Red made only of data entries. `NONE`: no test changed beside a production change; read the `## Red` exception. `FAIL`: head fails. Cost: one extra base build per PR (calibration: server 21–81 s, client import 4–28 s, plus the suite).
  - The gates config's `red` entries give each stack its command, by glob and folder. Maven: `{"glob": "server/**/src/test/**/*.java", "cwd": "server", "command": "./mvnw -B -ntp -q test -Dtest={classes} -Dsurefire.failIfNoSpecifiedTests=false"}` (`{classes}`: the class names, comma-joined). gdUnit: `{"glob": "client/test/**/*_test.gd", "cwd": "client", "command": "godot --headless --path . -s res://addons/gdUnit4/bin/GdUnitCmdTool.gd {-a res}"}` (one `-a res://…` per file, relative to the Godot project in `cwd`). `{tests}` gives paths relative to `cwd`; a prefix inside the braces repeats before each item; tests no entry covers run with `--run`.
  - `ERROR` (exit 2): no test ran, because the command could not start (exit 126/127) or the output has its stack's no-test line (`Ran 0 tests`, Maven `No tests to run`); fix the command or the config. It is no verdict.
- Scope: `RC scope --base <base> --head <sha> --files <globs of the Files cell> --body <pr.md> [--gates <gates.json>]`. A `protected:` line needs its label on the issue (`protected_paths`). A moved file lists its old path too, so a move out of a protected or out-of-Files path shows.
- Proof: `RC proof --body <pr.md> --run --gates <gates.json> --base <base> --cwd <tmp>` (or `--allow <cmd>` per allowlisted program). It also checks `## Red`, the `proof` block and the `Executor:` line, checks each path a line names before running it, fails a run whose output matches its stack's failure pattern at exit 0, and applies the stack lints (`--patterns` extends both); a line `not run` is re-run by hand or listed as Unverified.
- DoD: `RC dod --base <base> --head <sha> --review REVIEW.md`. Each hit names its `REVIEW.md` section: Scope, Correctness, Architecture and Security hits are blockers once confirmed; Docs and style hits are should-fix or nit. A deleted test file's assertions count as dropped, and so do a test file's moved out of the test globs; a rename inside them drops none.
- `red`, `scope`, `proof`, `feat-proofs` and `dod` read a `--gates`, `--review` or `--patterns` file inside the repository from git as `<base>` has it (`git show <base>:path`; `feat-proofs` without `--base`: `HEAD`), never from the checkout, so a PR cannot loosen its own rules by editing, deleting or relinking the file. Only the part of the path in front of the repository is resolved (an alias folder counts); from the repository root on the path stays lexical, so no link the head commits, on the file or a folder above it, can move it. A path that names a folder is a usage error (exit 2). `dod` takes `REVIEW.md` when base has one; run the tool from the repository root, since a working folder inside a linked one is already resolved. A file outside the repository is read from disk. Every diff the checks read is split only on newlines (one trailing CR dropped, so a rule anchored at `$` matches a CRLF line) and uses fixed `a/` and `b/` prefixes, raw file names and `--text --no-textconv --no-ext-diff`, so a `-diff` or `binary` attribute in the head's or base's `.gitattributes`, an unusual file name, a line separator inside an added line or the reviewer's diff-prefix config hides no line. A rules file or config the tool cannot read or use (a base that is not a commit, as in a shallow clone, bad JSON, not an object, a regex that does not compile, a value whose type crashes the check) exits 2, never the finding code 1; a wrong type that still iterates is not caught yet (#252). `dod` does not see a line-ending CR (it is dropped so a `$` rule matches a CRLF line), so a project that needs a rule about CRs enforces line endings in `.gitattributes`. Each run is its own process group, which a timeout, Ctrl-C, SIGTERM or SIGHUP kills whole.
- Compare the collected test count at head with base (the runner's summary line) and read the diff of every test file.
- Read the diff in risk order (security, input validation, control flow, public interfaces); report cited files absent from the diff, changed behavior no criterion asked for and changed code no test exercises.
- In Claude Code (Claude-specific) the calling session runs `/code-review <base>...HEAD` on the pushed head of any change above docs-only, in the background, and waits for its findings before the verdict (a forked review without the Skill tool asks the parent to run it). Confirm each finding at `path:line` on the clean checkout; an unconfirmed one goes under Unverified. Other executors apply `REVIEW.md` by hand; `/code-review` reads `CLAUDE.md`, not `REVIEW.md` (code.claude.com/docs/en/code-review, checked 2026-10-06).
- Closure records: the `living-docs` reference in skill `code-standards` — CHANGELOG, command-facing README changes, public API docs, FEAT status (derived, never typed), DEC/DEBT (the diff contradicts no accepted DEC) and an incomplete feature's flag.
- When the change touches `.java` or `.gd`, run `python3 ~/.ai-kit/platforms/tools/complexity.py --base <base>` after the gates and copy its lines to `Advisory:`; they never change the verdict.

## Verdict

```text
Target: <row, PR, FEAT or request> at <sha>    Tier: light | standard | full
Verdict: READY | PARTIAL | NOT READY
Gates: <command> → OK | FAILED (<literal excerpt>)
Scripts: red → OK | FAIL | NONE · scope → … · proof → … · dod → …
Reused: <result> — <record> — <why its inputs are unchanged>
Advisory: <complexity.py lines, or its missing-input notice>
| Criterion | Code | Test | Doc | Status |
|---|---|---|---|---|
| CA-n | path:line | path/command | path | met / missing / partial |
| Severity | Owner | path:line | Finding | close_when |
|---|---|---|---|---|
| blocker | apply | path:line | what goes wrong, for whom | `<command>` exits 0 / <observable> |
Unverified: <what and why>
Next step: <smallest action that changes the verdict>
```

- Owner `spec`: the spec is wrong or silent; the architect fixes it (`sdd-clarify` or the Plan) before the row. Owner `apply`: the finding carries its exact patch for the fix round. Owner `judgment`: a trade-off only the owner decides.
- `close_when` is a command or an observable the next round checks; the re-check (step 9) runs only those and the delta.
