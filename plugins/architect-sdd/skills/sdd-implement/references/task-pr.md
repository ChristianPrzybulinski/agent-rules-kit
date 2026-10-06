---
description: Executor contract for one task issue — scope, proof lines, self-check, PR body and stop conditions. Load before implementing an issue.
kind: detail
---

# Task issue — executor contract

## Scope

- The issue body is the spec, verbatim. Read the repo's `AGENTS.md`, then only the spec artifacts the issue's `Spec` line names plus the binding decisions that FEAT cites.
- Change only the paths in the `Files` cell, plus a `changelog.d/` fragment when the repo uses one — in that case never edit `CHANGELOG.md` directly.
- Run the `DoD` commands from `<Repository>/AGENTS.md` § Commands; they must pass.

## Proof lines

- Every proof line starts with a command from the project's allowlist (the issue's `Notes` names its location) and exits 0 at the pushed HEAD.
- A proof line contains no `$(...)`, no backticks and no redirection other than to `/dev/null`, and none of the words the project's gates refuse.
- Fixture secrets (tokens, keys, passwords) are low-entropy placeholders from the first commit — the secret scan reads every commit.

## Self-check before finishing

1. `git diff --name-only origin/main...HEAD` lists only paths inside `Files` (plus the fragment).
2. For each binding decision that touches the task, one line says where it is implemented.
3. Every proof command exits 0 at HEAD.
4. A needed path outside `Files` stops the work — name the exact path, never widen the cell silently.

## PR body

- Write the body to a file outside the worktree, with the sections What, Why, How I tested (literal command output), Proof (one allowlisted command per line) — last line `Closes <owner>/<docs-repo>#N`.
- Never push to `main`, force-push, rebase or merge.

## Stop conditions

- The spec is ambiguous, contradicts a decision, or the `Files` cell cannot hold the change: stop without guessing and record `[BLOCKER] <one line>` on the issue.
