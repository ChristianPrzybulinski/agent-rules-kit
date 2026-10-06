---
description: One-writer order, conflict re-check and push rules for review-loop verdicts.
kind: detail
---

# Review rules

## One writer per round

Only one side pushes per round, so the order depends on the findings.

- No `judgment` finding: post the flagged verdict for the item's SHA first, then push the `spec` and `apply` fixes. The new head has no verdict, so the loop sends the re-check.
- A `judgment` finding (mixed round): push first, then post the flagged verdict bound to the pushed head. Set `resolved_in` (your fix commit) on the findings you fixed and name the reviewed SHA in `summary`. The executor works from that head; do not push again until the next review.

## Pushing fixes

- A normal push on the PR branch: no force-push, no rebase. If the branch needs `main`, `git merge origin/main`; before committing the merge run `git diff --check` and grep for `^<<<<<<<`, because a merge with conflicts must never be concluded by `git add -A && git commit`.
- Run the proof block before pushing: the new head must pass the gates.
- Anything outside the issue's `Files` cell is fixed in its own PR to `main`.
- On a person's branch (lane human) never push: every finding goes in the verdict, with its exact patch when it is `apply`.

## Conflict re-check

After a conflict the executor merges `main` into the branch and the PR returns as a `review` item whose `last_verdict` is `approved`. Compare the net diff before and after (bases from `git merge-base origin/main <head>`): it must match except in the conflicted hunks, and there the result keeps both sides. A lost hunk is a `judgment` finding.

## Verdicts

`approved`, `flagged`, `needs-product` (a new `[DECISION]`, DEC or contract change) and `needs-human` (a finding that came back unchanged after the flagged rounds, `max_flagged_rounds` in the config).
