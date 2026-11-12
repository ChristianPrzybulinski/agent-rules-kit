---
id: KIT-046
title: "refresh.sh runs the pulled version of itself in the same run"
status: done
confirmed: "2026-11-12 (owner, chat of the kit review session: session-end kit proposal)"
issue: "#173"
pr: ""
---

# KIT-046 — refresh.sh runs the pulled version of itself in the same run

## Problem and evidence

[FACT] `platforms/tools/refresh.sh` runs `git pull --ff-only` on its own clone. Git replaces a changed file with a new
one, and bash keeps reading the copy it opened, so a run whose pull changes `refresh.sh` finishes with the old logic.

[FACT] On 2026-11-12, after pulling `02382ee` (KIT-038, which added the install branch for renamed plugins), the
first `bash ~/.ai-kit/platforms/tools/refresh.sh` printed only `refresh: reinstalled Claude plugin core@ai-kit (cache
differed from the kit)` (00:44:22Z). The second run printed `refresh: installed Claude plugin dev@ai-kit` and `sdd@ai-kit`
(00:45:02Z). Each of the night's twelve kit merges was then followed by two refresh runs.

## Change

- `platforms/tools/refresh.sh`: records `HEAD` before the pull. When the pull changed `platforms/tools/refresh.sh` or
  `platforms/tools/codex-bin.sh` (which it sources), it prints `refresh: the pull changed refresh.sh; running the new
  version` and `exec`s the pulled script with `AI_KIT_REFRESH_PULLED=1`. That run skips the fetch, the dirty-tree check
  and the pull, so the hand-over happens at most once.
- `platforms/tools/smoke.sh`: a fixture origin gets a commit that appends a line to `refresh.sh`. One refresh must print
  that line once and the hand-over line once; a second refresh with nothing to pull must not hand over.
- `platforms/tools/README.md` names the hand-over in the `refresh.sh` row.

## Proof

- `bash platforms/tools/smoke.sh`: OK with the change; with `refresh.sh` from `97e60ea` and the new smoke case it fails
  with `FAIL: smoke: the pulled refresh.sh did not run exactly once (changed)`.
- `bash platforms/tools/check.sh`, `python3 platforms/ci/validations/check_kit.py --links`,
  `python3 platforms/tools/gen_index.py --check`, the `platforms/ci/validations` unit tests and `gitleaks`.

## History

- 2026-11-12: confirmed (owner, in chat) and implemented.
