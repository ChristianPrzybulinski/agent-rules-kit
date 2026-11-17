---
description: Delivery-verdict detail of skill review — commands per step, recorded results, the clean-checkout fallback, the security probe, code-review, verdict format.
kind: detail
---

# Delivery steps

`RC` below is `python3 ~/.ai-kit/platforms/tools/review_checks.py`; it prints facts and exits 1 on a finding.

## Recorded results, the clean-checkout fallback and the security probe (steps 2–7)

- The required gates come from the repository's ruleset, `AGENTS.md` and README. Read their result recorded for the exact pushed head: the CI checks (`gh pr checks <n>`), or the project's gate record where it runs no CI on pull requests (a local or loop gate run naming the commit). Keep the literal failing excerpt.
- A recorded result (CI or gate run, or a log naming the commit) is reused while the files, dependencies, config, environment and assumptions it covers are unchanged; a new commit hash alone invalidates nothing. Write it on a `Reused:` line.
- Fallback, only when no such result exists for that head: run the gates once on a clean checkout. `git worktree list` first; create `<tmp>` with `mktemp -d`, then `git worktree add --detach <tmp> <sha>`; always finish with `git worktree remove --force <tmp> && git worktree prune`, even when a proof fails. Remove only a leftover `mktemp` worktree of an earlier validation; report any other extra worktree under Unverified.
- Gates run in a complete checkout: a gate that stops on a missing path in a sparse worktree is a failed run, never a pass. Kit fallbacks when the repository names none: `./mvnw -q spotless:check verify` (Java); `godot --headless --path . --import` plus the boot-proof grep of the `--quit` log from rule `godot.md` and the project runner (Godot); `platforms/tools/check.sh` or the project spec lint (docs/spec).
- Beyond that the reviewer runs nothing, except a targeted probe at a security boundary (full tier, or a diff where untrusted input enters): the hostile inputs that boundary must refuse, never a suite, in the same kind of clean checkout.

## Steps 3–7

- Red: read the `red` result recorded for the head by CI or the project's gate record; when none exists, run once on the clean checkout `RC red --base <base> --head <sha> --gates <gates.json> [--run '<test command from AGENTS.md, with {tests}>'] [--junit '<report glob>'] [--code-roots <glob>]`. The PR's `## Red` is the author's claim, never the record. The command comes from `AGENTS.md` or the gates config, never from the PR body. Per PR it needs one Red test and reports a class per test: `assertion` or `new-symbol` (a compile or import error on a name the PR's non-test diff adds, the normal Red of a new class) are Red; `runtime` and `missing-symbol` are not. Cost: one extra base build per PR (calibration: server 21–81 s, client import 4–28 s, plus the suite).
  - `OK`: a Red test, head green; changed tests that pass on base are normal. `EXEMPT`: no non-test change under the code roots, so base plus the tests equals head; nothing runs. `FLAG` (exit 3, judge, never block on it alone): only runtime errors, every test passing on base despite a production change, or a Red made only of data entries. `NONE`: no test changed beside a production change; read the `## Red` exception. `FAIL`: head fails.
  - The gates config's `red` entries give each stack its command, by glob and folder. Maven: `{"glob": "server/**/src/test/**/*.java", "cwd": "server", "command": "./mvnw -B -ntp -q test -Dtest={classes} -Dsurefire.failIfNoSpecifiedTests=false"}` (`{classes}`: the class names, comma-joined). gdUnit: `{"glob": "client/test/**/*_test.gd", "cwd": "client", "command": "godot --headless --path . -s res://addons/gdUnit4/bin/GdUnitCmdTool.gd {-a res}"}` (one `-a res://…` per file, relative to the Godot project in `cwd`). `{tests}` gives paths relative to `cwd`; a prefix inside the braces repeats before each item; tests no entry covers run with `--run`.
  - `ERROR` (exit 2): no test ran, because the command could not start (exit 126/127) or the output has its stack's no-test line (`Ran 0 tests`, Maven `No tests to run`); fix the command or the config. It is no verdict.
- Scope: `RC scope --base <base> --head <sha> --files <globs of the Files cell> --body <pr.md> [--gates <gates.json>]`. A `protected:` line needs its label on the issue (`protected_paths`). A moved file lists its old path too, so a move out of a protected or out-of-Files path shows.
- Proof: `RC proof --body <pr.md> --gates <gates.json> --base <base>` checks `## Red`, the `proof` block and the `Executor:` line and applies the stack lints (`--patterns` extends them) without running anything. A line whose result is recorded for the head (CI or the gate record) is not re-run. Only when no recorded result exists for that head, add `--run --cwd <tmp>` on the clean checkout (or `--allow <cmd>` per allowlisted program): it checks each path a line names before running it and fails a run whose output matches its stack's failure pattern at exit 0. A line `not run` is re-run by hand or listed as Unverified.
- DoD: `RC dod --base <base> --head <sha> --review REVIEW.md [--gates <gates.json>]`. Each hit names its `REVIEW.md` section; a confirmed hit blocks only as one of the four reasons of skill § 4 (a skipped test is (b), a secret in code is (c)), and every other hit goes to the follow-up issue. A deleted test file's assertions count as dropped, and so do those of a test file moved out of its runner's discovery pattern (the `red` globs of `--gates`, else the test globs: `tests/test_add.py` → `tests/test_add.py.off`); a rename its runner still collects drops none. Assertions are counted per CR line, so a CR-only test file counts each one.
- `red`, `scope`, `proof`, `feat-proofs` and `dod` read a `--gates`, `--review` or `--patterns` file inside the repository from git as `<base>` has it, never from the checkout (`feat-proofs` without `--base` reads `HEAD`; on a PR checkout pass `--base`); `dod` takes `REVIEW.md` when base has one. Run the tool from the repository root. Exit 2 is a usage error (a rules file or config it cannot read or use), never a finding; a failure the PR's own content causes is a finding naming the path. How it reads git objects and diffs, its process groups and every exit code: the module docstring of `review_checks.py`.
- Compare the collected test count at head with base (the summary line of the recorded runs) and read the diff of every test file.
- Read the diff in risk order (security, input validation, control flow, public interfaces); report cited files absent from the diff, changed behavior no criterion asked for and changed code no test exercises.
- In Claude Code (Claude-specific) the calling session runs `/code-review <base>...HEAD` on the pushed head of any change above docs-only, in the background, and waits for its findings before the verdict (a forked review without the Skill tool asks the parent to run it). Confirm each finding at `path:line` in the head's code; an unconfirmed one goes under Unverified. Other executors apply `REVIEW.md` by hand; `/code-review` reads `CLAUDE.md`, not `REVIEW.md` (code.claude.com/docs/en/code-review, checked 2026-10-06).
- Closure records: the `living-docs.md` reference in skill `sdd-implement` — CHANGELOG, command-facing README changes, public API docs, FEAT status (derived, never typed), DEC/DEBT (the diff contradicts no accepted DEC), the ENB catalog row of each changed contract (where `docs/spec/enablers/` exists) and an incomplete feature's flag.
- When the change touches `.java` or `.gd`, run `python3 ~/.ai-kit/platforms/tools/complexity.py --base <base>` (it reads the code, runs none of it) and copy its lines to `Advisory:`; they never change the verdict.

## Verdict

```text
Target: <row, PR, FEAT or request> at <sha>    Tier: light | standard | full
Verdict: READY | PARTIAL | NOT READY
Gates: <required check or command> → pass | fail (<literal excerpt>) | pending — recorded (<CI run or gate record>) | ran (clean checkout)
Scripts: red → OK | FAIL | NONE · scope → … · proof → … · dod → …
Reused: <result> — <record> — <why its inputs are unchanged>
Advisory: <complexity.py lines, or its missing-input notice>
| Criterion | Code | Test | Doc | Status |
|---|---|---|---|---|
| CA-n | path:line | path/command | path | met / missing / partial |
| Reason | Owner | path:line | Finding | close_when |
|---|---|---|---|---|
| (a)–(d) | apply | path:line | what goes wrong, for whom | `<command>` exits 0 / <observable> |
Follow-up: <issue link with every non-blocking finding>
Unverified: <what and why>
Next step: <smallest action that changes the verdict>
```

- Owner `spec`: the spec is wrong or silent; the architect fixes it (`sdd-clarify` or the Plan) before the row. Owner `apply`: the finding carries its exact patch for the fix round. Owner `judgment`: a trade-off only the owner decides.
- `close_when` is a command or an observable the coordinator's delta check (step 9) checks, with the delta only.
