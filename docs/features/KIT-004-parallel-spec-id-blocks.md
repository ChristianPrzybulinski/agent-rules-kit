---
id: KIT-004
title: "Parallel spec sessions take ids only from a block reserved per kind, REQ included"
status: confirmed
confirmed: "2026-10-07 (owner, chat of the Stratics E6 initial-screens architect session)"
issue: "#75"
pr: ""
---

# KIT-004 — Parallel spec sessions take ids only from a block reserved per kind, REQ included

## Problem and evidence

[FACT] On 2026-10-07 two architect sessions specified two stages of `stratics-docs` at the same time (E6 battle and E6
initial screens). The owner's session prompts reserved `DTEC-020` and `J-11` for one, and `FEAT-054`, `DTEC-021` and
`J-12` for the other, but no `REQ-F` ids. Both sessions had to promote rules to new REQs for their journeys.

[FACT] `sdd-constitution/references/sdd-process.md` § Identifiers and status says "Number sequentially per kind
namespace … never reuse", and `sdd-specify/SKILL.md` § 2 says "Choose the next unused `FEAT-nnn`". Both read `main`. On
`main` the last REQ was `REQ-F-086`, so both sessions would have taken `REQ-F-087`. The screens session avoided the
collision only by reading the other session's uncommitted worktree (`wt-e6-battle`: `REQ-F-087`…`089` untracked) and
taking `REQ-F-090`…`092`. The battle PR (stratics-docs#618) merged during the screens session and conflicted with it on
`docs/spec/spec.md` (adjacent index rows, resolved by hand), so the two sessions did meet on `main`.

## Change

- `plugins/architect-sdd/skills/sdd-constitution/references/sdd-process.md`, § Identifiers and status, gains:
  "When two or more spec sessions run against one specification at the same time, each session's prompt reserves a
  block of ids for every kind it may create (`FEAT`, `REQ-F`, `REQ-NF`, `DTEC`/`DGME`/`DPRO`, `DEBT`, `J`); a session
  takes ids only from its own block. A reserved id left unused stays a gap and is never reused."
- `plugins/architect-sdd/skills/sdd-specify/SKILL.md`, § 2: "Choose the next unused `FEAT-nnn` — or, when the session
  prompt reserves a block, the first unused id of that block; the same applies to the `REQ` ids you create."
- `plugins/core/skills/parallelize/SKILL.md` (if it lists parallel-session setup) points at the rule above.

## Proof

`bash platforms/tools/check.sh`, `bash platforms/tools/smoke.sh`,
`python3 platforms/ci/validations/check_kit.py --links`; a project whose spec lint requires contiguous ids would need
its own change first `[HYPOTHESIS: Stratics' check_spec.py does not; verify before relying on gaps]`.

## History

- 2026-10-07: confirmed (owner, chat).
