---
name: review
description: Completion verdict, claim check and PR gates. Use when asking “is it done?”, preparing a PR or testing a claim. Not for fixing failures (skill sdd-implement).
argument-hint: "[FEAT-xxx | spec path | request | claim or proposed fix | --pr <n>]"
triggers:
  - user
  - model
agent: reviewer
context: fork
background: false
allowed-tools:
  - read
  - grep
  - glob
  - exec
---

# Review

Verifies work someone else claims or proposes and reports a verdict with sources; it never fixes. Bugs with no named cause go to skill `investigate`.

| Argument | Mode | Procedure |
|---|---|---|
| `FEAT-xxx`, spec path or request (default) | completion verdict | §1–§4 below |
| one claim or proposed solution (default: the last relevant one) | claim check | `references/claim-check.md` |
| `--pr <n>` with a gates config | no-model PR gates | `references/pr-gates.md` |

## 1. Pin down the target

- For `FEAT-xxx`, read its acceptance criteria and linked `REQ-*` files.
- For a path or request, extract verifiable criteria; stop and ask for one to three criteria if none exist.
- Write the final criterion rows before inspecting the implementation.
- A reviewer gets the base, the head commit and the claims to check; the author's own verdict and reasoning stay out of its brief, so they cannot anchor the review.

## 2. Inspect what exists

- Run `git diff <base>...HEAD --stat` and inspect the changed files in risk order (security, input validation, control flow, public interfaces); report cited files absent from the diff, changed behavior no criterion asked for and changed code no test exercises.
- For each criterion, locate implementation, executable proof and required documentation.
- A criterion without an executable test or reproducible command is not met.
- Validate the pushed head on a clean checkout (`git worktree add --detach <tmp> <sha>`); local uncommitted state never counts. A result the author's report or PR lists is a claim until a record backs it: a CI or gate run, or a log a command wrote, naming the commit it ran on. Re-run there every proof without such a record and every proof whose inputs changed since it ran (files it covers, dependencies, config, environment, or an assumption it tested). Reuse a recorded result whose inputs are unchanged and write it on a `Reused:` line; a new commit hash alone invalidates nothing. A claimed result that neither a command nor a record reproduces is unverified; one that fails there makes the verdict `NOT READY`.
- After a correction, re-run and re-review the delta plus the assumptions it touches, not the whole change. Test evidence carries over; review authority does not: an approval binds to the head it reviewed, never to a later one, and an acceptance no reviewer gave is never recorded.
- Create `<tmp>` with `mktemp -d` and always finish with `git worktree remove --force <tmp> && git worktree prune`, even when a proof fails or the validation aborts; before you start, `git worktree list`; remove only a leftover whose path is a `mktemp` directory from an earlier validation, never a worktree you did not create, and report any other extra worktree under Unverified. A validation that leaves a worktree behind is not finished.
- A proof must be able to fail. A gate that passes on empty input (zero tests, zero schemas) is not proof; show it failing on a broken case. Compare the collected test count at the head with the base (the runner's summary line) and read the diff of every test file; a dropped count, a deleted or skipped test or a loosened assertion the PR does not name is a weakened check (agent `reviewer` step 4).

## 3. Run canonical gates

Read the repository's `AGENTS.md` and README for commands. Pick the gates by the impact row in skill `testing` § 6: a docs-only change runs the doc, schema, link or generator checks, not the code suites. Kit fallbacks:

| Stack | Gate |
|---|---|
| Java/Maven | `./mvnw -q spotless:check verify` |
| Godot | `godot --headless --path . --import`, then the boot-proof grep of the `--quit` log from skill `godot-standards` section 5 (`--quit` exits 0 after a `SCRIPT ERROR`), plus the project test runner |
| Docs/spec | `platforms/tools/check.sh` or project spec lint |

- Capture the literal failing excerpt; never replace it with “some tests failed.”
- Run the gates in a complete checkout of the repository. A sparse or partial worktree is for editing: a gate that stops there on a missing path (`can't open file`, `No such file`) is a failed run, never a pass, and under `set -e` it skips every later gate — rerun from a full checkout before the verdict.
- In Claude Code (Claude-specific) the calling session also runs `/code-review <base>...HEAD` on the pushed head before the verdict of any change above docs-only (when this skill runs forked without the Skill tool, run it from the parent session and hand its findings to the verdict); it runs as a background subagent and reports correctness bugs, so continue with the closure records while it runs and wait for its findings before §4. Confirm each finding at `path:line` on the clean checkout; a confirmed finding becomes a `missing` or `partial` row of the criterion table (or a `Gates:` line `code-review → FAILED (<finding>)` when it belongs to no criterion); an unconfirmed one goes under `Unverified`. In Devin or any other executor, apply the repository `REVIEW.md` (kit copy: `platforms/kits/github/REVIEW.md`) by hand instead. `/code-review` reads `CLAUDE.md`, not `REVIEW.md` (checked against code.claude.com/docs/en/code-review on 2026-10-06).
- Closure records: read the `living-docs` reference in skill `code-standards`. Check CHANGELOG, command-facing README changes, public API docs, FEAT status, DEC/DEBT (the diff contradicts no accepted DEC), and an incomplete feature's flag.

## 4. Issue the verdict

```text
Target: <FEAT, path or request>
Verdict: READY | PARTIAL | NOT READY
Gates: <command> → OK | FAILED (<literal excerpt>)
Reused: <result> — <record> — <why its inputs are unchanged>
Advisory: <complexity.py lines, or its missing-input notice>
| Criterion | Code | Test | Doc | Status |
|---|---|---|---|---|
| ... | path:line | path/command | path | met / missing / partial |
Unverified: <what and why>
Next step: <smallest action that changes the verdict>
```

- `READY`: every criterion is met and every gate passes. `PARTIAL`: at least one criterion is missing or partial while gates otherwise run. `NOT READY`: a gate fails or the target cannot be validated.
- When the change touches `.java` or `.gd`, run `python3 ~/.ai-kit/platforms/tools/complexity.py --base <base>` on the clean checkout after the gates (so a JaCoCo report is the one the gate just wrote) and copy its lines to `Advisory:`; they never change the verdict.
- An ambiguous criterion is a spec gap; route it to `sdd-clarify` rather than guessing.
- After three review-and-fix rounds that end `NOT READY` on the same criterion, stop: hand the owner the criterion, each attempt and the failing excerpt instead of starting a fourth round.

Done when: every criterion has observed code, proof and documentation status, all gates have literal results, and the verdict follows the rules above (other modes: the reference's own Done line).
