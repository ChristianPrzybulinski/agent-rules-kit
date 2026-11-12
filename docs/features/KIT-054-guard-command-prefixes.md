---
id: KIT-054
title: "The destructive-command guard sees commands behind assignments, paths, wrappers and line breaks"
status: done
confirmed: "2026-11-12 (owner in chat of the KIT-054 implementation session: \"Com quebra de linha (Recomendado)\" to the scope question before opening the issue)"
issue: "#189"
pr: "#190"
---

# KIT-054 — The destructive-command guard sees commands behind assignments, paths, wrappers and line breaks

## Problem and evidence

[FACT] The `core` PreToolUse guard (`plugins/core/hooks/hooks.json`) starts every pattern with the segment anchor
`S`, which matched only the start of the text, `;`, `&`, `|`, `$(`, or `sudo`/`xargs`/`time`/`env` followed by `-`
words. Any other prefix skipped every pattern; KIT-053 (#186, #187) listed it as not covered. Each form below, piped as
`{"tool_name":"exec","tool_input":{"command":"<form>"}}` into the guard command of `38a760b`, exits 0 (allowed):

| Prefix | Form that passed |
|---|---|
| assignment | `GIT_DIR=.git git branch -D x`, `FOO=1 BAR=2 rm -rf /`, `FOO= git reset --hard`, `AWS_PROFILE=prod terraform destroy` |
| path to the command | `/usr/bin/git branch -D x`, `/bin/rm -rf /`, `./bin/git reset --hard`, `~/bin/git reset --hard` |
| wrapper | `command git push --force`, `nice git reset --hard`, `nohup git push --force`, `exec git reset --hard`, `builtin command git push -f`, `timeout 5 git push --force`, `stdbuf -oL git reset --hard`, `ionice -c3 git reset --hard`, `doas git reset --hard` |
| wrapper option with a value | `sudo -u bob rm -rf /srv`, `nice -n 10 git reset --hard`, `timeout -s KILL 5 git push --force`, `xargs -I {} rm -rf {}`, `env -u HOME git reset --hard`, `env -i PATH=/bin git reset --hard` |
| segment head | `cd x` + line break + `git reset --hard`, `(rm -rf build)`, `{ rm -rf build; }`, `! git reset --hard`, `if true; then rm -rf build; fi`, `for f in a; do rm -rf $f; done` |
| `find -exec` | `find . -exec rm -rf {} +` |
| `curl \| sh` target | `curl -s x \| /bin/bash`, `curl -s x \| env bash` |

[FACT] The git global-option loop added by KIT-053 backtracked exponentially when `-C` and another `-` word alternate:
on `38a760b`, `git` + ` -C -a` × 20 + ` status` took 5.7 s (8.1 s at load average 16.8) and × 40 ran past 15 s, so
the guard hit its 10 s hook timeout and failed open (review note from the KIT-053 session).

[FACT] The flag scan `A` (`[^;&|]*\s`) crossed line breaks, so `rm -r build` + line break + `touch -f stamp` was
denied as `rm -rf`.

## Change

- `plugins/core/hooks/hooks.json` PreToolUse guard, the segment anchor `S`: a command starts at the start of the
  text, after `;`, `&`, `|`, a line break or `$(`, after `find`'s `-exec`, `-execdir`, `-ok` or `-okdir`, and, as
  before, at `sudo`, `xargs`, `time` or `env` anywhere. The anchor then accepts any sequence of prefix items `X`:
  - an assignment `NAME=value` (the value may be empty);
  - `(`, `{ ` or `! `;
  - `if`, `then`, `else`, `elif`, `do`, `while` or `until`, in lower case only, as bash reads them
    (`(?-i:…)` inside the case-insensitive guard);
  - the wrappers `sudo`, `doas`, `env`, `nice`, `nohup`, `exec`, `command`, `builtin`, `time`, `stdbuf`, `ionice` and
    `xargs`, each with options `O` (a `-` word and an optional value), and `timeout` with options and its duration.

  The command itself may be named by a path `D` (`/usr/bin/git`, `./bin/git`, `~/bin/git`).
- An option value in `O` cannot itself start a prefix item: it is never a `-` word, `(`, `{ `, `! `, an assignment, a
  keyword or a wrapper name. Each word therefore has one parse. Whitespace inside `X` and `O` is `[ \t]`, so a run of
  lines does not chain into one anchor.
- The flag scan `A` stops at an unescaped line break: `(?:\\\n|[^;&|\n])*[^\S\n]`. A backslash continuation still
  joins lines, so `rm \` + line break + `  -rf build` stays denied.
- The git global-option loop `G` gives each word one parse. `L` names the options that take the next word (`-C`,
  `-c`, `--git-dir`, `--work-tree`, `--namespace`, `--config-env`, `--attr-source`), and the generic `-` branch
  excludes them: `(?!L)-V`.
- The `curl | sh` pattern accepts `X` before the shell, so `| /bin/bash` and `| env bash` match.
- The KIT-020 merged-branch exception is unchanged: it accepts only the whole command `git branch -D <name>`, so
  `GIT_DIR=.git git branch -D <merged branch>` and `cd .` + line break + `git branch -D <merged branch>` are denied
  without calling `gh`.
- `platforms/ci/validations/hook_guard_cases.json`: 40 blocked forms (the table above, `timeout 5m rm -rf build`,
  `find . | xargs -n 1 rm -rf`, `command gh repo delete o/r --yes`, `nohup find . -delete`,
  `/usr/local/bin/docker volume rm data`, a mixed `cd repo && GIT_DIR=.git /usr/bin/git -C . push --force` and the
  backslash continuation). It also gains 18 allowed look-alikes: `echo "nice git reset --hard"`,
  `git log --grep "command git push --force"`, `make VAR=x`, one-line commit messages that name the forms,
  `xargs -I {} echo {}`, `timeout 5 git status`, `sudo -u bob ls`, `find . -exec ls {} +`,
  `if git diff --quiet; then echo ok; fi`, `cd x` + line break + `git status`, and `rm -r build` + line break +
  `touch -f stamp`, and a heredoc commit message whose body line starts with `Then git push --force`.
- `platforms/ci/validations/test_hooks_guard_merged_branch.py`: five more shapes that must be denied with a merged PR's
  head and no `gh` call: an assignment, `/usr/bin/git`, `command`, `nice` and a line break before
  `git branch -D <branch>`.
- `platforms/ci/validations/test_hooks_guard_compact.py`: `test_guard_time_is_bounded_on_contrived_input` runs four
  allowed commands and requires exit 0 under 1 s at best of 3: `git` + ` -C -a` × 40, `sudo` + ` -u x` × 40, 20,000
  line breaks, and a 1,000-line `KEY=value` heredoc.
- `docs/design.md`: the "Covered" and "Not covered" lines of the guard.

## Not covered

- A command passed as a string: `bash -c '…'`, `sh -c '…'`, `eval '…'`, `ssh host rm -rf /srv`. Backtick
  substitution: ``echo `rm -rf build` ``. Wrappers not listed: `caffeinate`, `watch`, `parallel`. Each exits 0 before
  and after this change.
- New false positive, accepted by the owner with the scope: a line inside a heredoc or a multi-line message that is a
  guarded command by itself (`cat > clean.sh <<EOF` with the line `rm -rf "$tmp"`), and
  `echo "find . -exec rm -rf {}"`. Both exit 2 after this change and exit 0 on `38a760b`. Shell keywords match
  in lower case only, so a message line such as `Then git push --force fails on a protected branch.` stays
  allowed. Wrappers match in any case, so a message line such as `Command git push --force stays denied.` is
  denied: on a case-insensitive macOS volume `Command`, `Nice` or `Time` runs `/usr/bin/command`,
  `/usr/bin/nice` or `/usr/bin/time`, and `38a760b` already matched `sudo`, `xargs`, `time` and `env` in any
  case.
- The `destructive SQL` and `curl | sh` patterns still scan across line breaks on purpose, so
  `psql <<EOF` + line break + `DROP TABLE x;` stays denied.
- Cost: one line with N consecutive wrappers costs O(N²), because each wrapper word is an anchor. `sudo ` × 100 + `echo`
  takes 0.19 s; × 400 takes 0.9 s (1.5 s at load average 16.8); × 1,000 takes 4.9 s (8.7 s at load average 16.8).
  Every other contrived input measured stays at or under 0.3 s.

## Proof

- Old guard (`hooks.json` from `38a760b`): 39 of the 40 new blocked cases exit 0, and the allowed case `rm -r build` +
  line break + `touch -f stamp` exits 2 (40 mismatches). The backslash continuation exits 2 on both guards. New guard:
  all 110 blocked and 75 allowed cases of `hook_guard_cases.json` match. The guard of `0b6fc37`, the first
  review head, denies the heredoc `Then git push --force` case (1 mismatch); `38a760b` allows it.
- `python3 -B -m unittest platforms/ci/validations/test_hooks_guard_merged_branch.py
  platforms/ci/validations/test_hooks_guard_compact.py`: 15 tests OK. With the old `hooks.json`, the five new shapes
  fail (allowed), and the timing test errors when `git` + ` -C -a` × 40 hits the 10 s run timeout.
- New guard: `git` + ` -C -a` × 40 takes 0.11 to 0.19 s.
- `bash platforms/tools/check.sh`, `CI=1 bash platforms/tools/check.sh`, `bash platforms/tools/smoke.sh`,
  `python3 platforms/ci/validations/check_kit.py --links`,
  `python3 -B -m unittest discover -s platforms/ci/validations -p "test_*.py"` and
  `gitleaks git --redact --log-opts="origin/main..HEAD"`.

## History

- 2026-11-12: left out of KIT-053 (#187) as not covered; the `G` backtracking was found in its review.
- 2026-11-12: scope confirmed (owner, chat, line breaks and `find -exec` included); issue #189, implemented in #190.
- 2026-11-12: review of #190 at `0b6fc37`: shell keywords made case-sensitive, so a capitalized prose line
  (`Then git push --force …`) is no longer denied.
