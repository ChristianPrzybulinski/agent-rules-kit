---
name: loop-child-implement
description: Implement one loop issue in its worktree. Use when given an issue number and repo. Not for fix rounds (skill loop-child-fix).
argument-hint: "<issue> <repo>"
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

Arguments: $ARGUMENTS (`<issue> <repo>`; if `$ARGUMENTS` appears literally in your context, read the issue and repo from the invocation text).

# Loop child: Implement

The Devin Cloud form of this skill is the playbook `platforms/kits/devin/playbooks/implement-issue.devin.md`.

Implement `<backlog-repo>#<issue>` in this worktree (`<repo>`). The spec is the issue body, verbatim: `gh issue view <issue> -R <owner>/<backlog-repo>`. Read this repo's `AGENTS.md`, then only the spec artifacts the issue names (its `Spec` line, the FEAT's binding decisions). Do not read the whole spec corpus.

## Rules

- Change only paths inside the issue's owned areas (the `Files` cell: globs or exact paths), the generated neighbours of an owned file (`*.uid`, `*.import`, `*.translation`) and one `changelog.d/` fragment instead of editing `CHANGELOG.md`. A protected path needs its label on the issue, and no changed file may overlap another open PR's diff (the architect waives with `overlap-ok`).
- One exception, an existing test your change breaks: when a test file outside the owned areas asserts the exact values your task changes, fix it and declare it in the PR body under `## Files widened`, one line per path (the path and why the change breaks it). The gates accept test paths only (`tests/**`, `src/test/**`, `**/tests/**`). Production code and build or config files outside the owned areas still mean `blocked`.
- Run the DoD commands from `AGENTS.md` Commands; they must pass.
- Scratch files (a commit message, notes) go under `.loop/`, never `/tmp`: writes outside the worktree are refused and end your run. Commit with `git commit -F .loop/commit-msg.txt` or `-m`. Delete a tracked file with `git rm <path>`; never run `rm` and never `mv` a file out of the worktree.
- Commit everything; `git status --porcelain` must be empty when you finish.
- Example secrets in fixtures are low-entropy placeholders from your first commit (for example `rt_AAAAAAAAAAAAAAAAAAAAAAAA`): the secret scan reads every commit of the PR and a realistic value cannot be removed without a force-push (see the project's review-loop README).
- Do not push and do not open the PR: the orchestrator does that after you finish.

## Before you finish

The gates re-run every check below on a clean checkout of your pushed commit.

1. After your last commit run `python3 <loop> proof-check --repo <repo> --issue <issue> --run` from the worktree root; it must end with `proof-check: ok ...`. Paste that line under How I tested in `.loop/pr-body.md`. The allowlist is `proof_allowlist` in the project's review-loop config plus the forbidden words; `proof-check` names the offending construct (see the project's review-loop README for database proofs).
2. List the FEAT's binding decisions; for each constraint that touches this task, say in one line where you implemented it.
3. If the proof needs a path outside the owned areas (a new test file, or the build or config file a new dependency needs), stop `blocked` and name the exact path; the architect widens the areas.

## PR body: write `.loop/pr-body.md` (never commit `.loop/`)

Sections in order: What (1-3 sentences), Why (link to the FEAT or issue), Files widened (only when you changed an existing test outside `Files`), How I tested (the last `proof-check` line plus any other literal output), Proof (a `proof` code block: commands that prove the issue's proof of completion, one per line, each exits 0, first word from `proof_allowlist`, `!` or `test` for negatives), then the last line `Closes <owner>/<backlog-repo>#<issue>`.

## Blockers

If the spec is ambiguous, contradicts a decision or the `Files` cell cannot hold the change, stop without guessing.

Last line of your output, exactly one JSON object: `{"status":"done","issue":<issue>}` or `{"status":"blocked","issue":<issue>,"reason":"<one line>"}`.
