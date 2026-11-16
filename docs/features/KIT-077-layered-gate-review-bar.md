---
id: KIT-077
title: "Layered gate: a fast PR gate, a full gate on main and release, and a review bar by risk"
status: confirmed
confirmed: "2026-11-15 (owner, chat of the coordinator session \"Revisão de regras e skills\": \"Sim, aplique\")"
issue: "#281"
pr: ""
delivered: "items 5–6 delivered; 1–4 after 13.0.0"
---

# KIT-077 — Layered gate: a fast PR gate, a full gate on main and release, and a review bar by risk

## Problem and evidence

[FACT] From #281, measured on the 13.0.0 pull requests:
- The required `ci` job took 5m51s on #272 (548 tests) and 14m06s on #261 (560 tests).
- A local full run took `Ran 674 tests in 632.920s` (#262 review).
- Review rounds: #261 three, #262 three, #260 two, each 10–35 min. #262's rounds chased bash spellings in a hygiene
  check (#280).
- The whole suite ran three times per PR: the author ran it, the reviewer ran it again, and CI ran it a third time.

## Change

The owner's test standard (2026-11-15): each test layer has one place and one trigger, CI is the gate, and a review is
one round that reads the diff against the FEAT plus the CI result. Six items; items 5 and 6 change what consumers read,
so they go into 13.0.0, and items 1–4 (the CI layering) may land after it.

1. Tag each test with its layer. *After 13.0.0.*
2. The required `ci` runs the PR layers in parallel, 3 min or less. *After 13.0.0.*
3. `ci-full` on push to `main`, nightly and on the release commit; `release.yml` refuses a tag without it.
   *After 13.0.0.*
4. Logic-only sync tests become in-process unit tests; the hook timing test moves to the performance layer (#278
   folds in). *After 13.0.0.*
5. **The review bar** (delivered):
   - skill `review`, its § 1 steps, § 2 and § 4: one round per PR; the reviewer reads the diff against the criteria
     plus the required gates' result recorded for the exact head (the CI checks, or the project's gate record where it
     runs no CI on pull requests, so a consumer without PR CI keeps its gate). Only when no such result exists for
     that head does it run the gates and the cited proofs, once, on a clean checkout; beyond that it runs nothing,
     except a targeted probe at a security boundary;
   - a finding blocks only for (a) an unmet acceptance criterion, (b) broken existing behavior (a failing test, a
     reproduced regression, or a weakened check the PR does not name), (c) a security gap where untrusted input
     enters, or (d) a rule lost in a migration. Everything else goes to one follow-up issue;
   - a small fix delta with no new mechanism is verified by the coordinator (red check plus a targeted probe), with no
     new round;
   - its reference `delivery-steps.md`: recorded results first, the clean checkout as the fallback, the security
     probe, and a verdict that lists gate sources, blocker reasons and the follow-up issue; agent `reviewer`
     (`plugins/guardrails/agents/reviewer.md`) follows the same rule (coordinator widening, 2026-11-16);
   - the `platforms/kits/github/REVIEW.md` template: § The review bar replaces § Important means, and § Scope checks
     the `Evals:` line.
6. **Local runs** (delivered):
   - skill `sdd-implement` § 2 and its references `test-gates.md` § 3 and `task-pr.md`: implementers run locally only
     the TDD loop (the unit and integration tests covering the changed files) and the linters, and CI runs the rest.
     Where a repository runs no CI on each push, its gate command or loop gate stands in;
   - a PR that changes skills or rules runs their evals by hand before it opens and cites the command and the score
     on an `Evals:` line;
   - `.github/CONTRIBUTING.md` and `.github/PULL_REQUEST_TEMPLATE.md` say the same for this repository.
     `evals.yml` stays dispatch-only, with no Anthropic secret.

## Proof

`python3 platforms/ci/validations/check_kit.py --links` (line limits, reference schema, links) and the tests that
cover the changed files; results in the PR. The evals run once before the 13.0.0 tag (coordinator).

## What would prove it wrong

A regression that reaches a consumer project and that the old full PR suite would have caught. Count these per
release in History.

## History

- 2026-11-15: confirmed (owner, through the coordinator session); issue #281.
- 2026-11-16: items 5 and 6 delivered for 13.0.0; items 1–4 follow the release.
