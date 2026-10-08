---
id: KIT-008
title: "Measure real conflicts with git merge-tree before deciding what runs in parallel"
status: done
confirmed: "2026-10-08 (owner, chat of the Stratics P1/P2 orchestrator session: \"7 aprovo\")"
issue: "#82"
pr: "#85"
---

# KIT-008 — Measure real conflicts with git merge-tree before deciding what runs in parallel

## Problem and evidence

[FACT] The kit serialized every pair of tasks that touch one file: `parallelize` § 4 fanned out `[P]` tasks "only
when file ownership is disjoint", and `sdd-tasks/references/waves-and-models.md` let two tasks share a wave "only when
their file sets are disjoint".

[FACT] Stratics measured that rule on 2026-10-07 (stratics-docs
`docs/collab/done/PROPOSAL-parallelism-unlock-2026-10-07.md` § 3). Each of 30 squash-merged task PRs (E5' server,
client and docs; P1 docs) was replayed onto its batch base with
`git merge-tree --write-tree --merge-base=<commit>^ <base> <commit>`, as if every agent had started together:

| Task PRs | Independent | Built on an earlier PR's lines | Conflicting pairs among independent | Fold conflicts |
|---|---|---|---|---|
| 30 | 21 (70 %) | 9 (30 %) | 0 of 48 | 0 |

The independent PRs shared files (`README.md` in 6 of 8 P1 PRs) and still merged cleanly; the 9 dependents extended
code an earlier PR created, which `Depends on` already ordered. The owner replaced the owned-area lock with a
real-conflict check (stratics-docs DPRO-011 amendment 2026-10-07c), and the measurement became a tool,
`platform/tools/parallel-sim/sim.py` (stratics-docs FEAT-053 T32, stratics-docs#759).

[FACT] The method was re-checked on git 2.54 in a throw-away repository on 2026-10-08: two commits editing lines 2 and
16 of one file replay alone with exit 0 and merge as a pair with exit 0; two commits editing line 2 merge as a pair
with exit 1 and name the file.

## Change

- `plugins/core/skills/parallelize/SKILL.md` § 4: "Fan out `[P]` tasks from skill `sdd-tasks` when they have no real
  conflict. Without evidence, disjoint file ownership is the test; a shared file is no conflict until a
  `git merge-tree` replay says so (`references/measure-conflicts.md`). Keep real dependencies and semantic hotspots
  (migration number, protocol version, error-code allocation) sequential."
- New `plugins/core/skills/parallelize/references/measure-conflicts.md`: the replay (alone, pairs, fold), how to read
  it, its limits (textual only; semantic hotspots keep a lock), and the Stratics numbers as the example.
- `plugins/architect-sdd/skills/sdd-tasks/references/waves-and-models.md` § Waves: two tasks may share a wave when
  their shared files are shown to merge cleanly by that replay; a semantic hotspot still separates them.

## Proof

`bash platforms/tools/check.sh`; `bash platforms/tools/smoke.sh`; `python3 platforms/ci/validations/check_kit.py --links`.

## History

- 2026-10-08: confirmed (owner, chat of the Stratics P1/P2 orchestrator session) and done.
