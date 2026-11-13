---
description: "Replay merged commits with git merge-tree to count real conflicts before serializing shared-file tasks or widening lanes. Load when planning parallel work."
kind: detail
---

# Measure real conflicts before parallelizing

Two tasks that share a file are not a conflict until git says so. Measure on the last batch before serializing work
for a shared file, before raising the number of parallel lanes, and at each batch end.

## Method (git ≥ 2.38; checked on 2.54)

Take the squash commits one batch merged into one repository, and its base `B` (the `main` commit the batch started
from).

1. **Alone.** Replay each commit `c` onto `B`, as if every agent had started together:
   `git merge-tree --write-tree --name-only --merge-base=c^ B c`.
   Exit 0: `c` is **independent** (keep the printed tree). Exit 1: `c` built on lines an earlier commit of the set
   wrote — a **dependency**, which `Depends on` must order.
2. **Pairs.** Merge every pair of independent trees over the base:
   `git merge-tree --write-tree --name-only --merge-base=B <tree a> <tree b>`.
   Exit 1 is a **conflicting pair**: those two need a merge order, not a lock.
3. **Fold.** Merge all independent trees one after the other over `B`: the merge-everything-at-the-end check.

`--name-only` prints the conflicted paths after the tree id. The runs only add objects to the clone; nothing is
checked out or pushed.

## Reading it

| Result | Decision |
|---|---|
| independent share high, no conflicting pair | shared files are no reason to serialize; run in parallel and merge continuously |
| a conflicting pair | keep both in flight; merge the earlier one first, then let the later one merge `main` |
| a dependent commit | the row needs `Depends on` (or a split), not a lane |
| many dependents on one file | split that hotspot file before widening the lanes |

## Limits

- Textual only. Two clean merges can still break each other: a migration number, a protocol version, an error-code
  allocation. Keep a lock on those semantic hotspots, and run the smoke on the merged base before each merge.
- A batch that already ran serialized shows what its rows did, not what parallel agents would have written.

## Example

[FACT] KIT-008, a consumer project, 2026-10-07: 30 task PRs of four batches; 21 independent (70 %), 0 of 48 pairs
conflicting although they shared files (`README.md` in 6 of 8 PRs of one batch), 9 dependent. A script that takes the
batch's commits runs the three steps above.
