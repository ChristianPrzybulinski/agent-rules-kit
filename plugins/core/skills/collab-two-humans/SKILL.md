---
name: collab-two-humans
description: "Condition → action rules for two people plus agents on one backlog. Use when a second human joins. Not for solo work."
triggers:
  - user
  - model
allowed-tools:
  - read
  - exec
---

# Two people and their agents — rules of the road

Ten condition → action rules for one backlog shared by two humans and their agents.

| Condition | Action |
|---|---|
| Starting work | the assignee field is the record; work splits by feature — each stage names one integration owner who runs its exit proof |
| Touching a file another owns | a `[PROPOSAL]` comment on the owning issue — never a parallel PR |
| Opening a branch | `feat/<issue>` (or the repo convention), one PR per task, ≤ 2 working days; merge `origin/main` daily; never rebase, never force-push |
| Before asking for review | run the same gates everyone runs and read your own diff; a failing PR stays a draft |
| Hitting a spec gap | `[BLOCKER]` comment on the issue + a proposed-fix spec PR; never guess past it |
| Reviewing | the architect reviews code PRs; the named second approver may take non-decision spec PRs; nobody approves their own PR |
| Reporting status | write it where everyone looks — the board, the batch-log issue, `blocked`/`needs-*` labels; never only in chat |
| Each working day | post the 10-minute async check-in (in flight / blocked / merged / next / needs the owner); allocation and stalled issues go to the weekly 30-minute sync |
| Letting an agent work | it writes only inside its own worktree and never pushes to the other person's branch; its spec is the repo's rules plus the issue body |
| Needing a machine-local value | keep it out of git: a git-ignored `*.local.*` file plus a committed `.example` |

Done when: both humans can reconstruct who owns what, what is in flight and what is blocked — from GitHub alone.
