---
id: KIT-007
title: "Agents' shell commands avoid three zsh traps; loops and JSON go to Python"
status: done
confirmed: "2026-10-08 (owner, chat of the Stratics P1/P2 orchestrator session: \"7 aprovo\")"
issue: "#81"
pr: ""
---

# KIT-007 — Agents' shell commands avoid three zsh traps; loops and JSON go to Python

## Problem and evidence

[FACT] The Stratics P1/P2 orchestrator session reported three shell slips to the owner on 2026-10-08, and the owner
confirmed this rule on that report. The agents run their commands in zsh, the default shell of the macOS hosts.

[FACT] The three traps reproduce on `zsh 5.9 (arm64-apple-darwin25.0)` with this script (2026-10-08):

```zsh
print -r -- "--body: see `echo RAN-AS-COMMAND` here"
for p in "wt-x feat/x"; do set -- $p; print -r -- "zsh: 1=[$1] 2=[$2]"; done
echo =====
```

```text
--body: see RAN-AS-COMMAND here
zsh: 1=[wt-x feat/x] 2=[]
repro.zsh:3: ==== not found
```

The same loop in bash prints `bash: 1=[wt-x] 2=[feat/x]`.

- A backtick inside a double-quoted argument is command substitution in every POSIX shell. A
  `gh pr create --body "…"` or `git commit -m "…"` whose text carries Markdown code spans runs each span as a command
  and posts its output in place of the span.
- zsh does not word-split an unquoted `$p` (no `SH_WORD_SPLIT`), so a pair loop that works in bash passes one word.
  [FACT] The Stratics architect notes record that on 2026-10-06 such a loop around `git worktree add` created a branch
  literally named `origin/main` (nothing was pushed).
- zsh expands a word that starts with `=` as the path of a command (`EQUALS`), so `echo =====` fails. The kit session
  that wrote this file hit it while printing a separator between two outputs (`(eval):1: ==== not found`).

## Change

- `plugins/core/AGENTS.md` § Work loop gains one line:
  "Shell (zsh is the macOS default): a backtick inside a double-quoted argument runs as a command
  (``--body "see `x`"`` runs `x`), so text with backticks goes in a file or a `<<'EOF'` heredoc; zsh does not
  word-split `$x` (``for p in "a b"; do set -- $p`` passes one word) and runs a leading `=` as a command lookup
  (`echo ===` fails), so loops over pairs, JSON and edits of several files go in a Python script."
- § Communication's "End with: done · unverified · concrete next step." folds into § Session's End line, which already
  names the same three items, so `AGENTS.md` stays within its 60-line limit (`check_kit.py`, `AGENTS_MAX_LINES`).

## Proof

`bash platforms/tools/check.sh`; `bash platforms/tools/smoke.sh`; `python3 platforms/ci/validations/check_kit.py --links`.

## History

- 2026-10-08: confirmed (owner, chat of the Stratics P1/P2 orchestrator session) and done.
