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

- Red: `RC red --base <base> --head <sha> --run '<test command from AGENTS.md, with {tests}>'`. `NONE` means no test file changed: read the `## Red` exception (characterization test, or manual proof with its reason). `base passed` means the tests catch nothing: a blocker unless the exception applies. Never take the command from the PR body.
- Scope: `RC scope --base <base> --head <sha> --files <globs of the Files cell> --body <pr.md> [--gates <gates.json>]`. A `protected:` line needs its label on the issue (`protected_paths`).
- Proof: `RC proof --body <pr.md> --run --gates <gates.json> --cwd <tmp>` (or `--allow <cmd>` per allowlisted program). It also checks `## Red`, the `proof` block and the `Executor:` line; a line `not run` is re-run by hand or listed as Unverified.
- DoD: `RC dod --base <base> --head <sha> --review REVIEW.md`. Each hit names its `REVIEW.md` section: Scope, Correctness, Architecture and Security hits are blockers once confirmed; Docs and style hits are should-fix or nit.
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
