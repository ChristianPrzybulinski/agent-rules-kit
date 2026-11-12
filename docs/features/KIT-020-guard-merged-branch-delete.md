---
id: KIT-020
title: "The destructive-command guard allows git branch -D on a merged PR's branch"
status: done
confirmed: "2026-11-12 (owner in chat of the kit backlog review session: \"Sim, os dois\" to implementing #113 and updating #138; the issue itself was confirmed 2026-10-30)"
issue: "#113"
pr: "#185"
---

# KIT-020 — The destructive-command guard allows git branch -D on a merged PR's branch

## Problem and evidence

[FACT] The `core` PreToolUse guard (`plugins/core/hooks/hooks.json`) denies every `git branch -D`. After a squash
merge that is the only command that removes the local branch: its tip is not reachable from the base branch, so
`git branch -d` refuses too. Every squash-merged PR leaves a local branch the agent cannot remove, and the owner runs
the command by hand (#113):

- 2026-10-30, `dev-game-studio/stratics#2979`, squash-merged as `84b86dbef`: the agent's
  `git branch -D fix/actions-gitleaks-cli` was denied with "ai-kit guard: git branch -D is destructive; ask the user
  to run or confirm it." The owner ran it; git printed `Deleted branch fix/actions-gitleaks-cli (was fe089823f)`, and
  `fe089823f` is the PR's merged head.
- `gh pr merge --squash --delete-branch` leaves the local branch when it is checked out in another worktree; an
  earlier stratics session listed the leftovers in the owner's to-do instead.
- 2026-11-12: the kit clone at `~/Developer/GitHub/agent-rules-kit` holds 34 local branches. Of the first eight that
  are not `main`, seven (`chore/release-11.1.0`, `fix/github-cli-connectivity`, `kit/kit-005-gates-need-full-checkout`,
  …) sit exactly at the `headRefOid` of a merged PR (#106, #91, #78, …); the eighth is this change's branch.

## Change

- `plugins/core/hooks/hooks.json` PreToolUse guard: when the only pattern that matched is `git branch -D` and the
  whole command is `git branch -D <name>` (spaces or tabs around it; one name of letters, digits and `_./+-`, not
  starting with `-`, without `..`), the guard runs, in the hook input's `cwd`:
  1. `git rev-parse --verify --quiet refs/heads/<name>` (timeout 2 s);
  2. `gh pr list --head <name> --state merged --json headRefOid` (timeout 5 s, `GH_PROMPT_DISABLED=1`, stdin closed).

  It exits 0 with no output, so the agent's normal permission flow still applies, only when a merged PR's
  `headRefOid` equals the branch tip. Every other result denies exactly as before: no such branch, `gh` missing,
  unauthenticated, offline or timed out, output that is not the expected JSON, no merged PR, or a different sha
  (commits made after the merge). The hook timeout goes from 5 s to 10 s (the `check_kit.py` ceiling), above the 7 s
  the two calls can take, so the inner timeouts decide and deny.
- Any other shape stays denied without calling `gh`: two names, a chained command (`&&`, `;`, a newline), `--`,
  a quoted or `$(…)` name, `--delete --force`, `-Df`. The check stays inline in `hooks.json`: `docs/design.md`
  ("One hook file", KIT-040) keeps scripts out because a script that is not found fails open.
- `platforms/ci/validations/test_hooks_guard_merged_branch.py` (new): 8 tests on a temporary repository with a stub
  `gh` and a `PATH` that holds only `bash`, `git`, `python3` and the stub, so an installed `gh` is never reached.
  They cover the allowed path (and the exact `gh` arguments and working directory), a different sha, an empty list,
  a failing `gh`, non-JSON output, a missing `gh`, a `gh` that hangs (denied before the hook timeout), an unknown
  branch and the other shapes above (both without a `gh` call).
- `platforms/ci/validations/check_kit.py` runs the guard cases in an empty temporary directory (process `cwd`,
  payload `cwd` and `GIT_CEILING_DIRECTORIES`), so a case like `git branch -D main` never reaches the network.
  `hook_guard_cases.json` gains two blocked cases: `git branch -D feat/merged other-branch` and
  `git branch -D feat/merged && git status`. The allowed path needs a repository and a stub `gh`, which the string
  cases do not have, so it lives in the unit test, as KIT-050's guard tests do; #113 had asked for both paths in the
  case table.
- `docs/design.md` and `CONTRIBUTING.md` name the exception and its test.

Not covered: `git -C <dir> branch -D <name>` passes the guard on `0124899` already (the pattern needs `git branch`
next to each other); that gap is older than this change and stays out of its scope. KIT-053 closes it.

## Proof

- `python3 -B -m unittest platforms/ci/validations/test_hooks_guard_merged_branch.py`: 8 tests OK. With `hooks.json`
  from `0124899` the allowed-path test fails (exit 2, denied) and the 7 denial tests pass, as they did before.
- Live, hook only (nothing deleted): with the payload `cwd` at `~/Developer/GitHub/agent-rules-kit`,
  `git branch -D chore/release-11.1.0` (tip `5acb6ce` = PR #106's merged head) exits 0 in 0.57 s, and
  `git branch -D kit/guard-merged-branch-delete` (no PR) exits 2 in 0.67 s.
- `python3 -B -m unittest discover -s platforms/ci/validations -p "test_*.py"`, `bash platforms/tools/check.sh`,
  `CI=1 bash platforms/tools/check.sh`, `bash platforms/tools/smoke.sh`,
  `python3 platforms/ci/validations/check_kit.py --links` and `gitleaks`.

## History

- 2026-10-30: proposed in a stratics closeout and filed as #113 (owner).
- 2026-11-12: confirmed (owner, chat) and implemented in #185.
