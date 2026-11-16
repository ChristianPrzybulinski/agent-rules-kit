---
description: "Executor contract for one task row: scope, widening, Red, proof, executor line, self-check, PR body, stops. Load before implementing a row."
kind: detail
---

# Task row — executor contract

## Scope

- The row (its issue body or TASK file) is the spec, verbatim. Read the repo's `AGENTS.md`, then only the spec artifacts the row's `Spec` line names plus the binding decisions that FEAT cites.
- Change only the paths in the `Files` cell, plus a `changelog.d/<id>.<type>.md` fragment of `- ` bullets when the repo uses one — in that case never edit `CHANGELOG.md` directly. The kit's `changelog_fragments.py --check` (`just changelog --check`) validates it; the `changelog-consolidate.yml` template moves fragments into `CHANGELOG.md` (KIT-084).
- `## Files widened` may add an existing test path outside Files that reads a changed file, one line each: `` `path`: why ``. It never adds production code, a new file or a changed assertion; `review_checks.py scope` refuses each.
- Run the `DoD` commands from `<Repository>/AGENTS.md` § Commands; they must pass.

## Red

- `## Red` names the new test and its failing line on the code before the change, as run: `` `tests/test_x.py::test_y` failed: AssertionError: 3 != 2 ``.
- Exceptions say which and why: `characterization: pins current behavior of <unit> before <change>`, or `manual: <check>, no honest test because <reason>`.
- `## Red` is the implementer's claim, which the PR always carries. The reviewer reads a red result recorded for the head by CI or the project's gate record, and when none exists reruns it once on a clean checkout: `review_checks.py red` copies the PR's test files onto the base and needs one test failing there on an assertion, or on a compile error naming a symbol the PR adds, then every test passing on the head. A test-only PR is exempt.

## Proof lines

- `## Proof` holds a fenced block tagged `proof`, one command per line. Every line starts with a command from the project's allowlist (the row's `Notes` names its location) and exits 0 at the pushed head.
- A proof line contains no `$(...)`, no backticks and no redirection other than to `/dev/null`, and none of the words the project's gates refuse.
- A round that cannot run the proof writes `not run: <why>` under the block; the gates run it before any verdict.
- Fixture secrets (tokens, keys, passwords) are low-entropy placeholders from the first commit — the secret scan reads every commit.

## Executor line

One line, real values only: `Executor: provider=<claude|codex|devin|human> tier=<model or tier> session=<CLI session or thread id>`. A placeholder, a guessed id or a missing line fails `review_checks.py proof`.

## Self-check before finishing

1. `git diff --name-only origin/main...HEAD` lists only paths inside `Files`, the fragment and the declared widenings.
2. For each binding decision that touches the task, one line says where it is implemented.
3. Every proof command exits 0 at HEAD, and the Red test now passes.
4. A needed path outside `Files` that is not an existing test stops the work — name the exact path, never widen the cell silently.
5. `git status --porcelain` is empty (under `commits_by: executor`).

## PR body

- Write the body to a file outside the worktree, with the sections What, Why, Red, How I tested (literal command output), Proof, and when they apply Files widened, Secrets to register and the capture of a visual change; then the executor line; last line `Closes <owner>/<docs-repo>#N` (or the TASK id under `tracker: none`).
- Commits follow Conventional Commits with `Refs: FEAT-nnn Tn`. Never push to `main`, force-push, rebase or merge; the item becomes done when its PR merges.

## Stop conditions

- The spec is ambiguous, contradicts a decision, or the `Files` cell cannot hold the change: stop without guessing and record `[BLOCKER] <one line>` on the item; the architect answers or fixes the spec and re-hands it.
- A fix round (mode fix) takes only the findings listed, on the same branch; a finding it cannot close goes back as `[BLOCKER]`, never as a silent partial.
