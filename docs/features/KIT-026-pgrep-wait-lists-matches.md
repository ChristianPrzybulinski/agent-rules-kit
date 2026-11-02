---
id: KIT-026
title: "A pgrep wait lists its matches before it waits"
status: done
confirmed: "2026-11-02 (owner, chat of the GitHub profile session: \"escreva a proposta\")"
issue: "#126"
pr: ""
---

# KIT-026 — A pgrep wait lists its matches before it waits

## Problem and evidence

[FACT] On 2026-11-02, before running the KIT-025 gates, a session waited for the one live Stratics loop gate with:

```sh
while pgrep -f 'stratics-review-loop/proof-' >/dev/null && [ $(( $(date +%s) - start )) -lt 3600 ]; do sleep 30; done
```

`pgrep -fl` with the same pattern listed helper processes (`-c import json, os, subprocess, sys, time`,
`print("ready")`, `pathlib.Path(...).touch`) started on 2026-10-26 in 8 leaked proof worktrees next to the live
gate's 5. Those leftovers never exit, so the wait could only end at its 3600 s deadline. The session stopped it and
ran the gates by hand after counting live gates another way.

[FACT] The same check, run from a second shell, also listed the waiting `zsh -c '... while pgrep -f ...'` process.
On macOS, `pgrep` skips itself and its ancestors (`man pgrep`, option `-a`), so a loop never matches its own shell.
Every other shell's count does match it, and so does a wrapper that holds the pattern (a gate's `sh -c` around its
Python, as the Stratics loop slot counter found on 2026-11-01).

[FACT] Reproduced on macOS (Darwin 25.6.0), zsh:

| Command | Result |
|---|---|
| `zsh -c 'pgrep -fl "kit026-selfmatch gates"; echo rc=$?'` | `rc=1`: no self-match |
| waiter `zsh -c 'while :; do sleep 1; : kit026-y gates; done' &`, then `pgrep -fl "kit026-y gates"` from another shell | lists the waiter |
| waiter holding `"[k]it026-z gates"`, then `pgrep -fl "kit026-z gates"` | lists nothing |
| `python3 -c '...' kit026-selfmatch gates &`, then `pgrep -fl "[k]it026-selfmatch gates"` | lists the Python process |

No kit file mentioned `pgrep` before this change.

## Change

`plugins/core/skills/parallelize/SKILL.md` § 3 Background long work gains one rule:

> Before waiting on `pgrep -f <pattern>`, list its matches once (`pgrep -fl`): the pattern also matches leftovers of
> earlier runs and any other shell or wrapper holding it. Narrow it to the processes meant, bracket one character
> (`'[l]oop.py gates'`) so the waiting shell stays out of other counts, and give the wait a deadline.

## Proof

The reproduction table above; `bash platforms/tools/check.sh`; `bash platforms/tools/smoke.sh`;
`python3 platforms/ci/validations/check_kit.py --links`; `gitleaks git --redact --log-opts="origin/main..HEAD"`.

## History

- 2026-11-02: confirmed (owner, chat) and done. The first proposal blamed a self-match of the waiting shell; the
  reproduction showed macOS `pgrep` excludes its ancestors, and the leftovers were the cause.
