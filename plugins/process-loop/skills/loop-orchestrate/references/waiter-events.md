---
description: Waiter exit codes and per-item actions of a review-loop batch for the architect session.
kind: detail
---

# Waiter events

Read the waiter's JSON, then act on the exit code.

| Exit | Event | Action |
|---|---|---|
| 0 | `work` | Handle every item (below), then re-arm the waiter. |
| 10 | `batch-complete` | Close the batch (skill step 8). |
| 11 | `stopped` | Report the batch status and stop. |
| 12 | `timeout` | Re-arm silently (a held batch returns only timeouts until `batch release`). |
| 13 | `error` | The host was unreachable for `max_poll_failures` polls in a row: tell the owner, then re-arm. |

## Items

- `review`: review the PR with skill `loop-review`.
- `merged`: one line to the owner: PR, issue, issues it unblocks.
- `armed`: the head carries the review status and auto-merge is armed; no action.
- `arm-failed`: auto-merge could not be armed (`detail`); no action, the loop merges when checks turn green.
- `conflict`: one line; the PR went back to the executor as a `fix-conflict` round and its re-check returns as a `review` item.
- `lane: human`: the issue is assigned to a person. Never push to that branch: every finding goes in the verdict with its exact patch when it is `apply`, and the author pushes. A conflict goes back to the author; `blocked` is the author's `[BLOCKER]` comment.
- `merge-failed`: one line with `detail`; the loop retries on the next poll, then look at the PR.
- `blocked`: the executor stopped with a question (read the latest issue comment). A spec gap: fix it now (issue body and FEAT row in a small spec PR), answer on the issue, remove the label, then the loop re-hands at once. A product question: notify the owner. "Ended without a result" is not a spec gap: check the worktree, remove the label.
- `needs-human`, `needs-product`, `wait`: notify the owner (the platform's notification tool or chat, 200 chars at most), write the reason in chat, keep the loop running.

## Dispatch events

The waiter already did the mechanical step; `<loop> batch status` lists running and queued children.

- `child-started`, `child-done`: one line (issue, round kind, model; the PR or pushed fix). Gates and review arrive as later items.
- `child-blocked`: the waiter commented the reason and labelled the issue `blocked`; handle it as `blocked`.
- `child-failed`: `relaunched: true` is one line, no action. `relaunched: false` with `cause: permission`: a tool call outside the executor's allow list ended it; tell the owner which command needs an allow rule (never edit that config yourself) and leave the issue `blocked`. With `cause: no-result` the re-hands are spent: treat it as `blocked`.
- `child-stalled`: read the end of `log` and tell the owner; never kill a child (`batch stop` ends all).
- `dispatch-error`: a git or host step failed (`stage` launch, publish or reap, with `detail`); tell the owner. A rejected non-fast-forward publish means someone pushed to the PR branch while the child ran: merge the remote branch in its worktree and push by hand, or drop the commits. Never push to a PR branch while a child is running or queued for it.
- `stalled` (batches without dispatch): ask the owner to look at the session; `<loop> rehand --issue <n>` hands it again.
