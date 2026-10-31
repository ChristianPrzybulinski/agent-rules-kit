---
id: KIT-023
title: "One Codex CLI lookup that honors CODEX_BIN"
status: done
confirmed: "2026-10-31 (owner, chat of the portability Phase 1 session)"
issue: "#116"
pr: "#119"
---

# KIT-023 — One Codex CLI lookup that honors CODEX_BIN

## Problem and evidence

[FACT] `bootstrap.sh`, `refresh.sh` and `doctor.sh` each defined `codex_bin()`. On 2026-10-31 the three copies had the same MD5. Each searched `codex` on `PATH`, then `/Applications/ChatGPT.app` and `/Applications/Codex.app`, then `~/.cache/codex-runtimes`, with no override (portability assessment, row 1.10).

[FACT] A machine could not name its Codex CLI: one outside those paths was not found, and with several installed the kit took the first. A lookup fix had to land three times.

## Change

- New `platforms/tools/codex-bin.sh` holds the one `codex_bin()`. `bootstrap.sh`, `refresh.sh` and `doctor.sh` source it from their own directory. Run directly, it prints the CLI the kit would use, or exits 1.
- Lookup order: `$CODEX_BIN`, `codex` on `PATH`, the CLI bundled in ChatGPT.app or Codex.app, then any executable named `codex` under `~/.cache/codex-runtimes` or the two apps. `AI_KIT_NO_CODEX_CLI=1` still finds none.
- A `CODEX_BIN` that is not executable prints `WARN: CODEX_BIN=<path> is not an executable file` on stderr and finds none. The kit does not fall back to another CLI, because a wrong explicit path should show rather than be replaced silently.
- `smoke.sh` runs `codex-bin.sh` with `CODEX_BIN`, runs `refresh.sh` with `CODEX_BIN` naming a stub that is not on `PATH` (the stub marketplace upgrades), and runs it with a `CODEX_BIN` that does not exist (the warning shows and the `codex` on `PATH` is not used).
- `README.md` (Codex section) and `platforms/tools/INDEX.md` describe the helper and the order.

## Proof

- `bash platforms/tools/check.sh`
- `bash platforms/tools/smoke.sh`
- `python3 platforms/ci/validations/check_kit.py --links`
- On the maintainer's Mac: `platforms/tools/codex-bin.sh` prints `/opt/homebrew/bin/codex` (exit 0); `CODEX_BIN=/nope` prints the warning (exit 1); `AI_KIT_NO_CODEX_CLI=1` exits 1.

## History

- 2026-10-31: confirmed (owner, portability Phase 1 chat).
- 2026-10-31: gates green at host load 10–12 (`check_kit.py --links`, `check.sh`, `smoke.sh`).
