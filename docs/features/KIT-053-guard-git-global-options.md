---
id: KIT-053
title: "The destructive-command guard sees git commands with global options before the subcommand"
status: confirmed
confirmed: "2026-11-12 (owner in chat of the KIT-053 implementation session: \"Sim, abrir\" to opening the issue and the PR)"
issue: "#186"
pr: ""
---

# KIT-053 — The destructive-command guard sees git commands with global options before the subcommand

## Problem and evidence

[FACT] The `core` PreToolUse guard (`plugins/core/hooks/hooks.json`) wrote nine of its git patterns as
`git\s+<subcommand>`, so a git global option between `git` and the subcommand skipped them. Found while implementing
KIT-020 (#185): a test showed `git -C . branch -D feat/x` passing the guard on `main`. Each form below, piped as
`{"tool_name":"Bash","tool_input":{"command":"<form>"}}` into the guard command of `4044bb5`, exits 0 (allowed):

| Pattern | Form that passed |
|---|---|
| `git branch -D` | `git -C . branch -D x`, `git --bare -C repo.git branch -D old` |
| `git push --force` | `git -C repo push --force`, `git -c 'user.name=A B' push -f` |
| `git reset --hard` | `git -c k=v reset --hard`, `git --git-dir .git --work-tree . reset --hard HEAD~1` |
| `git clean -f` | `git --git-dir=.git clean -fd` |
| `git checkout -- <path>` | `git --work-tree . checkout -- f`, `git -C repo checkout .` |
| `git restore` | `git --no-pager restore src/main.gd` |
| `git stash drop` | `git -C "my repo" stash drop`, `git --no-optional-locks -C repo stash clear` |
| `git filter-repo` | `git -C repo filter-branch --tree-filter 'rm x' HEAD` |
| `git lfs migrate` | `git -C repo lfs migrate import --everything` |

The `git --no-verify` pattern (`git\b[^;&|]*\s…`, KIT-050) already allowed anything between `git` and the flag:
`git -C repo commit --no-verify -m x` exits 2 on `4044bb5`.

## Change

- `plugins/core/hooks/hooks.json` PreToolUse guard: two new pieces, `V` (one shell word without `;`, `&` or `|`
  outside quotes: plain characters, backslash escapes, `"…"` and `'…'`) and
  `G = S + git (global option)* + whitespace`, where a global option is `-C`, `-c`, `--git-dir`, `--work-tree`,
  `--namespace`, `--config-env` or `--attr-source` followed by a separate value, or any other word that starts with
  `-` (`--git-dir=…`, `--no-pager`, `-P`, `--bare`, `--no-optional-locks`, `--literal-pathspecs`, …). The nine
  patterns above start with `G` instead of `S + git\s+`; what follows the subcommand is unchanged, so
  `git -C repo branch -d merged`, `git -C repo push origin feat` and `git log --grep "reset --hard"` stay allowed.
  `\x27` stands for the single quote, because the Python source sits inside `python3 -c '…'`. Every piece of `V` starts
  with a different character and a word ends at whitespace, so the regex does not backtrack across words.
- The KIT-020 merged-branch exception is unchanged: it accepts only the whole command `git branch -D <name>`, so
  `git -C . branch -D <merged branch>` now matches the `git branch -D` pattern and is denied without calling `gh`.
- `platforms/ci/validations/hook_guard_cases.json`: 16 blocked cases with global options (one or more per pattern) and
  13 allowed look-alikes (`-C` with a safe subcommand, `--grep "reset --hard"`, an alias value `"reset --hard"`, a
  commit message that names `git push --force`).
- `platforms/ci/validations/test_hooks_guard_merged_branch.py`: three more shapes that must be denied with a merged
  PR's head and no `gh` call: `git -C . branch -D <branch>`, `git --no-pager branch -D <branch>` and
  `git -c core.x=y branch -D <branch>`.
- `docs/design.md`: the "Covered" line names git global options; the "Not covered" line names the command prefixes the
  segment anchor does not know.

Not covered (every pattern, not only git, so out of this scope): a prefix the segment anchor `S` does not list.
On `4044bb5` and after this change, `GIT_DIR=.git git branch -D x`, `/usr/bin/git branch -D x`,
`command git push --force` and `nice git reset --hard` exit 0.

## Proof

- Old guard (`hooks.json` from `4044bb5`): the 16 new blocked cases exit 0 (16 mismatches); the 13 allowed cases
  exit 0. New guard: all 70 blocked and 57 allowed cases of `hook_guard_cases.json` match.
- `python3 -B -m unittest platforms/ci/validations/test_hooks_guard_merged_branch.py`: 8 tests OK; with the old
  `hooks.json` the three new shapes fail (`0 != 2`, allowed).
- `bash platforms/tools/check.sh`, `CI=1 bash platforms/tools/check.sh`, `bash platforms/tools/smoke.sh`,
  `python3 platforms/ci/validations/check_kit.py --links`,
  `python3 -B -m unittest discover -s platforms/ci/validations -p "test_*.py"` and
  `gitleaks git --redact --log-opts="origin/main..HEAD"`.

## History

- 2026-11-12: found while implementing KIT-020 (#185), left out of its scope.
- 2026-11-12: confirmed (owner, chat).
