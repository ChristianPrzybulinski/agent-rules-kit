---
id: KIT-022
title: "launchd refresh finds ~/.local/bin and logs skipped CLIs"
status: done
confirmed: "2026-10-31 (owner, chat of the portability Phase 1 session)"
issue: "#115"
pr: ""
---

# KIT-022 — launchd refresh finds ~/.local/bin and logs skipped CLIs

## Problem and evidence

[FACT] `platforms/kits/launchd/ai-kit.refresh.plist` gave the refresh job `PATH=/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin`. On 2026-10-31 `launchctl print gui/$UID/ai-kit.refresh` showed that `PATH` on the maintainer's Mac.

[FACT] The terminal runs `~/.local/bin/claude` (2.1.287, a symlink into `~/.local/share/claude/versions/`); launchd found `/opt/homebrew/bin/claude` (2.1.288). A Mac without the Homebrew copy finds no `claude` under launchd.

[FACT] `refresh.sh` updated the Claude plugins only `if command -v claude`, with no `else`, and the Codex step only when a `codex` was found. `/tmp/ai-kit.refresh.log` held only `refresh: <sha> <date> main` lines, so a skipped step left no trace (portability assessment, row 1.9).

## Change

- `ai-kit.refresh.plist`: `PATH` is `@HOME@/.local/bin:/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin`. `~/.local/bin` comes first so launchd runs the same `claude` as a login shell that lists it first.
- `bootstrap.sh` substitutes `@HOME@` with `$HOME` next to `@KIT@`, escaping `&` and `|` the same way.
- `refresh.sh` prints `skip: refresh: no codex CLI found; Codex marketplace not upgraded` and `skip: refresh: claude CLI not found on PATH <PATH>; Claude plugins not updated` on stdout, which launchd writes to `/tmp/ai-kit.refresh.log`. The exit code does not change.
- The plan also named a `devin` skip line. `refresh.sh` has no Devin step (`doctor.sh` checks the Devin plugin), so a line for it would report a step that never runs; it is left out.
- `smoke.sh`, macOS only: reruns `bootstrap.sh` with a stub `launchctl` first on `PATH`, lints the rendered plist with `plutil -lint`, and checks that no placeholder remains, that `PATH` starts with the throwaway home's `.local/bin` and that `launchctl bootstrap` was called. The stub keeps the machine's real agent untouched. On every OS it runs `refresh.sh` with no agent CLI and checks both `skip:` lines.
- `platforms/kits/launchd/README.md` and `platforms/tools/INDEX.md` describe the new `PATH` and the skip lines.

A plist installed before this change keeps the old `PATH` until `bootstrap.sh` runs again; `refresh.sh` does not re-render it.

## Proof

- `bash platforms/tools/check.sh`
- `bash platforms/tools/smoke.sh`
- `python3 platforms/ci/validations/check_kit.py --links`
- `launchctl print gui/$UID/ai-kit.refresh` before and after the smoke run shows the same program and `PATH`.

## History

- 2026-10-31: confirmed (owner, portability Phase 1 chat).
- 2026-10-31: gates green at host load 10–12; `launchctl print gui/$UID/ai-kit.refresh` and the installed plist (sha256 prefix `fd75f6d561527dd1`) were the same before and after `smoke.sh`.
