---
id: KIT-003
title: "smoke.sh: the fixture commit must not start background maintenance"
status: done
confirmed: "2026-10-07 (owner, chat of the Stratics architect session)"
issue: "#73"
pr: "#74"
---

# KIT-003 — smoke.sh: the fixture commit must not start background maintenance

## Problem and evidence

[FACT] `bash platforms/tools/smoke.sh` stopped at `FAIL: smoke: bootstrap failed` on the owner's clone, four runs out of
four on 2026-10-07: `fatal: failed to copy file to '…/home/.ai-kit/.git/objects/…': No such file or directory`. The
same run passed on a fresh clone and in CI. `GIT_TRACE=1` on the fixture commit shows
`git maintenance run --auto --quiet --detach` (Git 2.54, Apple Git-157). About one second later, the fixture's ~650
loose objects are packed, while `bootstrap.sh` runs `git clone` on the fixture. An object packed mid-copy fails the
clone, so this is a race, not repository state.

## Change

`platforms/tools/smoke.sh`: the fixture commit runs with `-c maintenance.auto=false -c gc.auto=0`, with a comment that
names this race.

## Proof

Three local runs of `bash platforms/tools/smoke.sh` on the owner's clone → `smoke: OK`; four of four had failed before.
`bash platforms/tools/check.sh` → `check: OK`.

## History

- 2026-10-07: confirmed (owner, chat) and implemented in #74.
