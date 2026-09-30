---
description: "`git worktree` add/list/remove/prune: parallel work on 2 branches without stash, pitfalls (.git is a file, shared hooks). Load when suggesting a parallel checkout."
trigger: model_decision
verified: "2026-09-30"
sources:
  - https://git-scm.com/docs/git-worktree
---

# Git worktrees


`git worktree` allows multiple working directories linked to the same repository, each on a different branch.

## Commands

```bash
git worktree add ../project-fix feature/fix-x   # create worktree (new or existing branch)
git worktree list                               # list worktrees and their HEADs
git worktree remove ../project-fix              # remove (requires a clean tree; --force deletes)
git worktree prune                              # clean metadata of worktrees already deleted from disk
```

## When to use

- Parallel work on 2 branches without `stash`: hotfix on `main` while a feature stays open in another directory.
- Run a branch's slow tests/builds while editing another.
- Review the exact checkout of a tag/commit (`--detach`) without touching the main tree.

## Pitfalls

- **The same branch cannot be checked out in two worktrees** (blocked; use `--detach` or another branch).
- In a worktree, `.git` is a **file** pointing to `.git/worktrees/<name>` of the main repo — tools that assume a `.git` directory may fail.
- Hooks live in the main repo's `.git/hooks` — **shared** by all worktrees.
- Two directories open: IDEs may index both (memory/CPU usage doubles); commits and staging are isolated, but the history is the same.
- Submodules need `git submodule update` per worktree.

Note: idea absorbed from obra/superpowers `using-git-worktrees` (MIT).
