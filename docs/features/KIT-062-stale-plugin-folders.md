---
id: KIT-062
title: "The stale kit path scan covers every plugins/ folder of the kit's history"
status: done
confirmed: "2026-11-13 (owner, chat of the kit review session: \"Sim, fazer\" for adding `plugins/infra-` to the scan; the other missing folders follow the same rule and the PR waits for the owner's merge)"
issue: "#215"
pr: "#216"
---

# KIT-062 — The stale kit path scan covers every plugins/ folder of the kit's history

## Problem and evidence

[FACT] `platforms/tools/sync-project.sh` says its `STALE_KIT_PATHS` lists the obsolete kit paths of "layouts 1.x to
11.x", and `sync-project.sh --check` fails a consumer repository that cites one. After KIT-061 the list named six
`plugins/` folders (`ai-kit/`, `core/`, `sdd/`, `dev/` and `architect-*`). `git log origin/main --name-only` at
`49f675e` shows 17 folders under `plugins/` before `guardrails`; 11 were missing: `all/`, `dev-core/`, `dev-godot/`,
`dev-java/`, `extras/`, `infra-core/`, `infra-github/`, `infra-persistence/`, `process-loop/`, `quality-core/` and
`quality-security/` (the pattern `plugins/dev/` does not match `plugins/dev-java/`). The KIT-061 review found Stratics
`docs/spec/decisions/DPRO-006-preservacao-acervo-legado.md:50` citing
`plugins/infra-core/skills/git-lfs/references/git-lfs-and-binaries.md`, a dead path no check flags.

[FACT] A `git grep` with the scan's regex and exclusions on Stratics `stratics-docs` `origin/main` `52277530c` finds
29 lines in 12 files with the completed list (14 with the KIT-061 list): 1 live instruction (`AGENTS.md:33`), 8 lines
in 6 decision records (DPRO-001, DPRO-006, DPRO-015, DTEC-001, DTEC-002, DTEC-003), 1 in
`platform/review-loop/templates/README.md` and 19 in done records and a changelog fragment. Stratics has no
root-level `plugins/` folder, so no Stratics path of its own matches. `sync-project.sh --check` itself was not run on
Stratics.

## Change

`platforms/tools/sync-project.sh`: `STALE_KIT_PATHS` adds `plugins/all/`, `plugins/dev-`, `plugins/extras/`,
`plugins/infra-`, `plugins/process-loop/` and `plugins/quality-`. `platforms/ci/validations/test_sync_project.py`
adds `test_older_plugin_folders_fail` (one citation of each of the 11 folders; it fails with the KIT-061 list,
`AssertionError: 0 != 1`); `test_current_plugin_layout_passes` keeps `plugins/guardrails/` clean.

Consequence for Stratics (its next sync to 12.x, outside the kit): each of the 29 lines gets its current path or the
`<!-- kit-path-ok -->` marker; the 8 decision-record lines are owner edits.

## Proof

`bash platforms/tools/check.sh`, `python3 platforms/ci/validations/check_kit.py --links`,
`python3 -B -m unittest platforms/ci/validations/test_sync_project.py`, `bash platforms/tools/smoke.sh` and
`gitleaks git --redact --log-opts=origin/main..HEAD`; results in the PR body.

## History

- 2026-11-13: confirmed (owner, chat).
- 2026-11-13: done (PR #216; owner "Sim, merge" for all 11 folders).
