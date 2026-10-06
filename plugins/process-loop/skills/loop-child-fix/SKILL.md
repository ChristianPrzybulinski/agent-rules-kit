---
name: loop-child-fix
description: Apply a loop fix round from .loop/findings.json. Use when a PR has gates or verdict findings. Not for new issues (skill loop-child-implement).
argument-hint: "<repo>#<pr>"
triggers:
  - user
disable-model-invocation: true
allowed-tools:
  - read
  - grep
  - glob
  - exec
  - edit
---

Arguments: $ARGUMENTS (`<repo>#<pr>`; if `$ARGUMENTS` appears literally in your context, read the repo and PR from the invocation text).

# Loop child: Fix round

The Devin Cloud form of this skill is the playbook `platforms/kits/devin/playbooks/fix-round.devin.md`.

`.loop/findings.json` is a gates result (`"schema": "<project>-gates/v1"`), an architect verdict (`"schema": "<project>-verdict/v1"`) or a conflict notice (`"schema": "<project>-conflict/v1"`). It is the whole scope of this round; do nothing else. Scratch files (a commit message, notes) go under `.loop/`, never `/tmp`: writes outside the worktree are refused and end your run. Leave `.loop/` files in place; delete a tracked file with `git rm <path>`, never with `rm` or a `mv` out of the worktree.

You start without the implementer's conversation. First read `.loop/pr-body.md` (its `Closes` line names the issue), `git log --oneline origin/main..HEAD` and `git diff origin/main...HEAD`. Open the issue only if a finding needs it.

## Gates result

Fix every result with `"ok": false`:

- Missing proof block or `Closes` line: fix `.loop/pr-body.md`.
- Scope violation: revert the out-of-scope paths. One exception: an existing test file the task's change breaks may stay changed if declared in `.loop/pr-body.md` under `## Files widened` (the path and why); the gates accept test paths only (`tests/**`, `src/test/**`, `**/tests/**`). A `protected path ... needs label` or `overlaps #...` failure is not yours: report `blocked` and name the label it needs.
- Failed proof command: fix the code until it passes.

## Verdict

For each finding whose severity is not `info`:

- `owner: apply`: apply `patch` (or `fix`) verbatim, no redesign. Exception: skip it on a `<backlog-repo>` PR (the verdict's `pr` starts with `<backlog-repo>#`), where the architect already applied it in the head the verdict names.
- `owner: judgment`: make the smallest change that satisfies `claim` and `fix`.
- `owner: spec`: skip it; the architect fixes those.

## Conflict notice

The architect approved this PR, then `main` moved and the PR conflicts. Nothing may be lost.

1. `git fetch -q origin && git merge origin/main`.
2. Resolve every conflicted file so both sides keep their behaviour: `main`'s side is reviewed work from other PRs, this branch's side is the approved change. Never delete a line from either side to end the conflict; where both edited the same lines, combine them. In `changelog.d/` keep every fragment.
3. If the two sides contradict each other and keeping both needs a design choice, run `git merge --abort` and stop: `{"status":"blocked","reason":"conflict needs a design choice: <files>"}`.
4. Run every command in the proof block of `.loop/pr-body.md`; all must exit 0.
5. Commit the merge with git's default message; `git status --porcelain` must be empty. Do not push. Last line: `{"status":"done","closed":["conflict"]}`.

A round that only changes `.loop/pr-body.md` (for example the proof block) leaves no commit: update the PR body anyway (`gh pr edit ... --body-file .loop/pr-body.md`). The loop re-runs the gates when the proof block changes, even on the same head.

## Then

1. Run the `close_when` of every finding you handled, then `python3 <loop> proof-check --repo <repo> --run` (it reads the issue from the `Closes` line); it must end with `proof-check: ok ...`; paste that last line under How I tested in `.loop/pr-body.md`.
2. Commit with the message `fix(review): <finding ids or "gates">`; `git status --porcelain` must be empty. Do not push.
3. Last line of your output, exactly one JSON object: `{"status":"done","closed":["F1","F2"]}` or `{"status":"blocked","reason":"<one line>"}`.
