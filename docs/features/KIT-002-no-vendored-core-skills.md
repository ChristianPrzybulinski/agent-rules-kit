---
id: KIT-002
title: "Vendored projects do not copy core's skills"
status: done
confirmed: "2026-10-07 (owner, chat of the Stratics architect session)"
issue: "#71"
pr: "#72"
---

# KIT-002 — Vendored projects do not copy core's skills

## Problem and evidence

[FACT] A project synced with `sync-project.sh --vendor-skills` enables only `core@ai-kit` in `.claude/settings.json`,
because the guard hook lives only in the plugin. The sync also copied core's own skills into `.claude/skills/`, so a
session opened inside the repository loads `collab-two-humans`, `parallelize`, `session` and `tokens` twice: from the
plugin and from the copy. On 2026-10-07 the three Stratics repositories each vendored exactly those four skills next to
`"core@ai-kit": true` (compared `.claude/skills/` with `plugins/core/skills/`).

## Change

- `platforms/tools/sync-project.sh`: `skill_dirs` skips the `core` plugin, so `--vendor-skills` and `--check` neither
  copy nor expect core's skills; a resync removes the marked copies (a marked directory out of the list is removed).
- `platforms/ci/validations/test_sync_project.py`: the install test expects no core skill under `.claude/skills/`; the
  drift, profile-switch and collision tests use `github-cli` instead of `tokens`.
- `platforms/tools/smoke.sh`: the vendored marker count and the extra-file checks follow.

## Proof

`python3 -B -m unittest discover -s platforms/ci/validations` → OK; `bash platforms/tools/check.sh` → `check: OK`;
`bash platforms/tools/smoke.sh` → `smoke: OK` on a clean clone of `main` with the change applied.

## History

- 2026-10-07: confirmed (owner, chat) and implemented in #72.
