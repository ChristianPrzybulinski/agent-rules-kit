---
description: Pre-existing findings of sdd-check - when a finding predates the change, the base and since arguments, the report and the task-chain case.
kind: detail
---

# Pre-existing findings (#380, #388, #392)

A finding the change under check did not write is listed apart and does not block, so drift older than the change stops costing a run each time. The check is a read-only fork with no `exec`, so it reads git only through arguments the calling session pastes, like `validator=`.

## Arguments

- `base=<commit>`: the merge base of the branch with the project's default branch (`git merge-base HEAD <default branch>`). The caller also pastes `base-diff=` with `git diff --unified=0 <base>..HEAD -- <spec_root>`.
- `since=<commit>`: the commit that added the NEED's `clarify: refined` History line, the oldest match of `git log --format=%H --reverse -S'clarify: refined' -- <NEED file> | head -1`. For a re-run after fixes it is instead the commit the previous run checked (its `HEAD`), so the run checks only the lines changed since; the fork keeps no memory, so the caller supplies it, and a second full run per scope and change is not made. The caller also pastes `since-diff=` with `git diff --unified=0 <since>..HEAD -- <spec_root>`. It narrows the functional rows of the full scope (`SKILL.md` Scope).
- Without `base=` and `base-diff=` the check cannot claim `pre-existing`: every finding keeps its severity and blocks. Without `since=` the full scope runs the functional rows on the whole FEAT scope, as before: with `sdd.needs: false`, with `sdd.flow: feat-only`, for a FEAT or version block opened for a routed fix, or when the NEED has no `refined` line.

## When a finding is pre-existing

All three hold:

1. Each cited line lies outside the added or changed lines of `base-diff=`: the change did not write it, and the text there is the base's text.
2. The same finding holds on the base: the rule fails on that text without the change's lines (judge it from the file and the diff; the evidence is the cited `path:line` plus the `base=` commit).
3. The change does not make it worse (more instances, a longer chain, a wider scope), and no REQ the change adds or amends depends on it. Otherwise it blocks as usual.

## Report

A `Pre-existing` list follows the findings table: `# | row | severity | file:line | problem | base evidence`. Those findings are not rows of the table and are not in the counts by severity or in `blocked:`. The `all` scope has none: it never blocks, and `docs/spec/baseline.json` covers its old findings. Routing: `sdd-intake` § 4 (a fix row, a spec fix or one owner question); never fix them inside the NEED or FEAT under check.

## `task-chain` after a fix row

`task-chain` is a `check_spec.py` rule: its `FAIL:` line arrives in `validator=` (`SKILL.md` § 1 a) as `longest Depends on chain is N rows (...), above sdd.max_chain M`. It is `pre-existing` when the FEAT only becomes `in-progress` because the change adds a fix row, and the chain does not lengthen: read the FEAT's task table, drop the rows `base-diff=` adds, recompute the longest `Depends on` chain, and compare it with N. Equal: pre-existing, as `high` on the list. Longer, or the fix row sits on the chain: it blocks.
