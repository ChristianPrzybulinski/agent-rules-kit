<!-- section names verified 2026-10-06 against docs.devin.ai/product-guides/creating-playbooks; the file name and playbook_id use are unverified -->
# Implement one backlog issue in a worktree

## Overview

Implement `<backlog-repo>#<issue>` in this worktree (`<repo>`). The spec is the issue body, verbatim: `gh issue view <issue> -R <owner>/<backlog-repo>`. Read this repo's `AGENTS.md`, then only the spec artifacts the issue names (its `Spec` line, the FEAT's binding decisions); never the whole spec corpus. Do not push and do not open the PR: the orchestrator does that after you finish.

## What's Needed From User

- The issue number `<issue>`, the repo name `<repo>` and the path of the review-loop script `<loop-script>`.
- A worktree on the issue's branch, with `gh` authenticated through the Devin secrets store.
- An issue whose `Files` cell (owned areas, globs or exact paths) can hold the whole change; otherwise the answer is `blocked`.

## Procedure

### Setup

1. Read `AGENTS.md`, the issue body and the artifacts its `Spec` line names.
2. List the FEAT's binding decisions; for each one that touches this task (fields, limits, conventions), note where you implement it.
3. Keep scratch files (commit message, notes) under `.loop/`, never `/tmp`; `.loop/` is never committed.

### Task

1. Change only paths inside the `Files` cell, the generated neighbours of an owned file (`*.uid`, `*.import`, `*.translation`) and one `changelog.d/` fragment instead of editing `CHANGELOG.md`.
2. Run the DoD commands from `AGENTS.md` (Commands); they must pass.
3. Use low-entropy placeholders for example secrets in fixtures from your first commit (for example `rt_AAAAAAAAAAAAAAAAAAAAAAAA`).
4. Commit everything with `git commit -F .loop/commit-msg.txt` or `-m`; delete a tracked file with `git rm <path>`.

### Delivery

1. After the last commit run `python3 <loop-script> proof-check --repo <repo> --issue <issue> --run` from the worktree root; it must end with `proof-check: ok ...`.
2. Write `.loop/pr-body.md`: What (1-3 sentences), Why (link to the FEAT or issue), Files widened (only when you fixed an existing test outside the `Files` cell; one line per path: the path and why the task's change breaks it), How I tested (the last `proof-check` line plus any other literal output), a `proof` code block (one command per line, each exits 0, first word from the review-loop config `proof_allowlist`, use `!` or `test` for negatives), then `Closes <owner>/<backlog-repo>#<issue>`.
3. If the proof needs a path outside the owned areas (a new test file, or the build/config file a new dependency needs), stop with `blocked` and name the exact path; the architect widens the areas.
4. Print the JSON object of the Specifications as the last line.

## Specifications

- `git status --porcelain` is empty.
- Every proof line exits 0 on a clean checkout of the pushed head: the loop's gates re-run them, so a failure here comes straight back.
- Every changed file is inside the `Files` cell, a generated neighbour or the fragment. Exception: an existing test file your change breaks may change if it is declared under Files widened; the gates accept test paths only (`tests/**`, `src/test/**`, `**/tests/**`). Production code and build/config files (`pom.xml`, `application.yml`) outside the owned areas still mean `blocked`.
- The last line of the output is exactly one JSON object: `{"status":"done","issue":<issue>}` or `{"status":"blocked","issue":<issue>,"reason":"<one line>"}`.

## Advice and Pointers

- A protected path needs its label on the issue, and no changed file may overlap another open PR's diff (the architect waives with `overlap-ok`); only the gates check both.
- `proof-check` names the offending construct when a proof line leaves the allowlist (see the project's review-loop README for database proofs).
- Writes outside the worktree are refused and end your run; so are `rm` and a `mv` out of the worktree (`/dev/null` included).
- If the spec is ambiguous, contradicts a decision or the `Files` cell cannot hold the change, stop without guessing and report `blocked`.

## Forbidden Actions

- Push, force-push or open the PR.
- Edit a path outside the `Files` cell (except as allowed above) or edit `CHANGELOG.md` directly.
- Commit a realistic secret in a fixture: the secret scan reads every commit of the PR and a value committed once cannot be removed without a force-push.
- Run `rm`, `mv` out of the worktree, or write under `/tmp`.
