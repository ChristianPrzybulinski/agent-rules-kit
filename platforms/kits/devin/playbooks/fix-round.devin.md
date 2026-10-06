<!-- section names verified 2026-10-06 against docs.devin.ai/product-guides/creating-playbooks; the file name and playbook_id use are unverified -->
# Fix round - apply `.loop/findings.json` on this branch

## Overview

`.loop/findings.json` is a gates result (`"schema": "<project>-gates/v1"`), an architect verdict (`"schema": "<project>-verdict/v1"`) or a conflict notice (`"schema": "<project>-conflict/v1"`). It is the whole scope of this round; do nothing else. You start without the implementer's conversation.

## What's Needed From User

- A worktree on the PR branch with `.loop/findings.json` and `.loop/pr-body.md` (its `Closes` line names the issue).
- The path of the review-loop script `<loop-script>` and the repo name `<repo>`.

## Procedure

### Setup

1. Read `.loop/pr-body.md`, `git log --oneline origin/main..HEAD` and `git diff origin/main...HEAD`; open the issue only if a finding needs it.
2. Keep scratch files under `.loop/`, never `/tmp`; delete a tracked file with `git rm <path>`.

### Task

1. Gates result: fix every result with `"ok": false`. Missing proof block or `Closes` line: fix `.loop/pr-body.md`. Scope violation: revert the out-of-scope paths, except an existing test file your task's change breaks, declared under Files widened in `.loop/pr-body.md` (test paths only). A `protected path ... needs label` or `overlaps #...` failure is not yours: report `blocked` and name the label. Failed proof command: fix the code until it passes.
2. Verdict: for each finding whose severity is not `info`, apply `owner: apply` verbatim (patch or fix, no redesign), except on a `<backlog-repo>` PR (the verdict's `pr` starts with `<backlog-repo>#`) where the architect already applied it; make the smallest change that satisfies `claim` and `fix` for `owner: judgment`; skip `owner: spec`.
3. Conflict notice (the architect approved, then `main` moved; nothing may be lost): `git fetch -q origin && git merge origin/main`; resolve every file so that both sides keep their behaviour (never delete a line from either side to end the conflict; in `changelog.d/` keep every fragment); if keeping both needs a design choice run `git merge --abort` and stop with `{"status":"blocked","reason":"conflict needs a design choice: <files>"}`; run every command of the proof block; commit with git's default merge message.

### Delivery

1. Run the `close_when` of every finding you handled, then `python3 <loop-script> proof-check --repo <repo> --run`; it must end with `proof-check: ok ...`; paste that last line under How I tested in `.loop/pr-body.md`.
2. Commit with `fix(review): <finding ids or "gates">`; a conflict notice keeps the merge commit.
3. A round that only changes `.loop/pr-body.md` leaves no commit: update the PR body anyway with `gh pr edit ... --body-file .loop/pr-body.md`; the loop re-runs the gates when the proof block changes.

## Specifications

- `git status --porcelain` is empty and nothing is pushed.
- Every command of the proof block exits 0.
- The last line of the output is exactly one JSON object: `{"status":"done","closed":["F1","F2"]}`, `{"status":"done","closed":["conflict"]}` or `{"status":"blocked","reason":"<one line>"}`.

## Advice and Pointers

- Apply a patch verbatim; a different change needs a different finding.
- Writes outside the worktree are refused and end your run; so are `rm` and a `mv` out of the worktree.
- When the findings contradict each other or the spec, stop with `blocked` and say which.

## Forbidden Actions

- Push, force-push or open a PR.
- Edit outside the findings' scope or the `Files` cell, or widen a test path without declaring it.
- Run `rm`, `mv` out of the worktree, or write under `/tmp`.
- Commit a realistic secret in a fixture.
