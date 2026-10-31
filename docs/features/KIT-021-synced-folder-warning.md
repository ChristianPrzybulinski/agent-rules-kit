---
id: KIT-021
title: "Warn when a repository sits in a cloud-synced folder"
status: done
confirmed: "2026-10-31 (owner, chat of the portability Phase 1 session)"
issue: "#114"
pr: "#117"
---

# KIT-021 — Warn when a repository sits in a cloud-synced folder

## Problem and evidence

[FACT] On 2026-10-30 the owner's workspace sat in iCloud Desktop & Documents (`~/Documents/GitHub`). `fileproviderd` was syncing about 2M Git items. A single rename of the whole folder blocked in the kernel and failed with `ETIMEDOUT` after 3 h 13 min, with nothing moved. Renaming each top-level entry separately moved 1.06M items in 92 s.

[FACT] On 2026-10-31 a launchd job could stat and write a file by path in iCloud Drive, but listing the folder failed with "Operation not permitted" (portability assessment, row 0.1).

[FACT] Nothing in the kit detected the situation; the owner found it by hand. The plan named this KIT-020; #113 already holds that ID, so it is KIT-021.

Detection on this Mac, 2026-10-31: `xattr -p com.apple.file-provider-domain-id ~/Documents` prints `com.apple.CloudDocs.iCloudDriveFileProvider/<uuid>` (exit 0); `~/Developer` has no such attribute (exit 1); `~/Library/CloudStorage/` holds `iCloudDrive-iCloudDrive (…)`.

## Change

- `plugins/core/hooks/hooks.json` gains a `SessionStart` group, matcher `^startup$`, timeout 5. Its inline `python3 -c` command resolves the payload's `cwd` (symlinks followed) and checks it against:
  - `~/Library/Mobile Documents` (iCloud Drive) and `~/Library/CloudStorage` (File Provider clients such as Dropbox, Google Drive and OneDrive);
  - on macOS, `~/Documents` and `~/Desktop` when `xattr -p com.apple.file-provider-domain-id` prints a value (iCloud Desktop & Documents). `xattr` runs only when the working directory is under one of them, so a repository elsewhere starts no subprocess;
  - the Dropbox folders in `info.json`. The Dropbox help center gives `~/.dropbox/info.json`, `%APPDATA%\Dropbox\info.json` or `%LOCALAPPDATA%\Dropbox\info.json`, with `personal`/`business` entries and a `path` key;
  - the `%OneDrive%`, `%OneDriveCommercial%` and `%OneDriveConsumer%` folders. [HYPOTHESIS] These variables come from Microsoft Q&A threads; no Microsoft reference page defines them.

  On a match it prints `{"systemMessage": m, "hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": m}}`. The message `m` names the folder and says to move the repository out, for example to `~/Developer`. Every path exits 0: a warning, never a block. `~/Documents/GitHub` as a symlink to `~/Developer/GitHub` resolves out of the synced folder and stays silent.
- `platforms/tools/sync-project.sh` reruns that hook command for its target repository (`{"cwd": <repo>}`) and prints the message as `sync: warning: …` on stderr, in install and `--check` mode, without changing the exit code. A detector that exceeds the hook's timeout or prints nothing yields no line. Codex has no hooks, so this is the agent-neutral path. The detector exists once.
- `platforms/ci/validations/check_kit.py` accepts `SessionStart` (matcher must match `startup`, timeout at most 10) and runs `hook_session_start_cases.json`: 13 cases on a throwaway `HOME`. A stub `xattr` answers the iCloud cases, because macOS refuses writes to `com.apple.file-provider-domain-id` (`xattr -w` exits 1 with "Operation not permitted"). The three iCloud cases run on macOS only.
- `test_sync_project.py` covers the `sync-project.sh` warning and its absence.
- `README.md` (platform table), `docs/design.md`, `docs/maintenance.md` and `platforms/ci/validations/INDEX.md` name the hook and its case table.

## Proof

- `bash platforms/tools/check.sh`
- `bash platforms/tools/smoke.sh`
- `python3 platforms/ci/validations/check_kit.py --links` (reports 25 hook cases: 12 post-edit, 13 session-start)
- `python3 -m unittest platforms/ci/validations/test_sync_project.py`
- Manual pipe on this Mac with the hook command: `{"cwd": "$HOME/Documents"}` prints the warning, while `{"cwd": "$HOME/Documents/GitHub"}` (a symlink to `~/Developer/GitHub`) and `{"cwd": "$PWD"}` print nothing; all exit 0.

## History

- 2026-10-31: confirmed (owner, portability Phase 1 chat): the call sites are the session hook and `sync-project.sh`, and it warns instead of blocking.
- 2026-10-31: one `check_kit.py --links` run at load average 18 timed out the `unsynced folder` case against the 5 s budget; the same command takes 0.09 s at load 16. The hook now runs `xattr` only under `~/Documents` or `~/Desktop`, and `sync-project.sh` treats a timeout as no warning instead of a Python traceback.
- 2026-10-31: the pre-merge rerun at load average 20 timed out the same case again. Cause: `check_kit.py` ran each case with only `PATH` and `HOME`; without `TMPDIR` the macOS `/usr/bin/python3` shim skips its xcrun cache, so `python3 -c pass` took 0.20 s instead of 0.04 s at load 7, and 0.86 s on the first call. The detector itself took 0.12 s. A real session has `TMPDIR`, so the harness now passes it through.
