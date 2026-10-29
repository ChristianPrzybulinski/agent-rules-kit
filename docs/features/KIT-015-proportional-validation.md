---
id: KIT-015
title: "Validation and review sized by impact, with recorded evidence reuse and a shorter closeout"
status: done
confirmed: "2026-10-29 (owner, Stratics process-simplification implementation brief in chat)"
issue: "#100"
pr: "#101"
---

# KIT-015 — Validation and review sized by impact, with recorded evidence reuse and a shorter closeout

## Problem and evidence

[FACT] Stratics T20 (dev-game-studio/stratics#2914) ran the full review-loop suite twice:
`full-loop.log` reports "Ran 1782 tests in 478.379s" (FAILED, failures=2) and `full-loop-final.log` reports "Ran 1783
tests in 398.712s" (OK). Focused checks closed the correction delta. `review-regressions-green.log` ran 67 tests in
1.477 s and `history-regression-green.log` ran 9 tests in 2.910 s; the reviewer checked only the correction commit.

[FACT] The kit and the project disagreed on evidence reuse. `validate-implementation` § 2 said "Re-run there every
proof command the author's report or PR lists". The Stratics `AGENTS.md` section "Session provenance and review reuse"
says not to repeat successful checks whose inputs are unchanged. The T20 process review lists this conflict
(`process-review.md`, row "Written rules conflict on evidence reuse").

[FACT] `testing` § 6 said only "Run the narrow relevant test first, then the repository gate". That line had no
docs-only row, so a prose change got the same gate as shared integration code. Core `AGENTS.md` § Boundaries said
"run project tests/lint before saying "done"" for every change.

[FACT] `session` start and review modes ran the handoff mode "when work is committed, pending or transferring". A
handoff file then duplicated the issue or PR that already recorded the state; T20's process review calls this
"Administrative duplication".

[FACT] The `session` kit-proposal signals covered only gaps: a missing reference, a repeated procedure, a repeated
correction, a mis-trigger or a template. No signal pointed at a rule or step that cost time without changing the
outcome, so a closeout never proposed removing one (owner request in chat, 2026-10-29).

## Change

- `plugins/dev-core/skills/testing/SKILL.md` § 6: a three-row impact table. Docs only runs the doc, schema, link or
  generator checks. Bounded code reproduces the failure, runs the affected tests, adds a regression test where it
  matters and gets one independent review. Shared integration, authorization, persistence or migration adds boundary
  and negative tests, the broad suite once, one review and the existing approvals. Impact is judged by behavior, not
  extension: "agent instructions, permissions, workflows and executable config are code when they change runtime or
  security behavior". The section also gains reuse ("a new commit hash alone invalidates nothing") and the
  correction-delta rule.
- `plugins/quality-core/skills/validate-implementation/SKILL.md`:
  - § 2 re-runs proofs that have no record (a CI or gate run, or a log naming the commit) and proofs whose inputs
    changed. It reuses the rest on a `Reused:` line. After a correction it checks the delta.
  - Review authority stays bound to the reviewed head: "an approval binds to the head it reviewed, never to a later
    one, and an acceptance no reviewer gave is never recorded".
  - § 3 picks gates by the impact row. `/code-review` runs for any change above docs-only.
  - § 5's verdict gains `Reused:`.
- `plugins/quality-core/agents/reviewer.md`: step 2 and the report follow the same record-and-reuse rule; a reused
  result is listed with its record, and the verdict binds to the reviewed `<sha>` only.
- `plugins/core/skills/session/SKILL.md`:
  - The start and review modes point to the issue or PR that records pending work. They run the handoff mode only when
    no such record exists, and they cite recorded proof instead of re-running it.
  - Follow-ups live in "the issue, PR or handoff record".
  - The kit-proposal step also looks for "a rule or step that cost time without changing the outcome".
- `plugins/core/skills/session/references/kit-proposal.md`:
  - A simplification signal row: remove, merge or narrow the rule in the file that owns it, kit or project.
  - The search lists every copy of the rule, and any control the step still provides stays.
  - The proposal block gains the `simplification` kind.
- `plugins/core/AGENTS.md`, still 60 lines:
  - § Boundaries: "run the project checks the change's impact requires (skill `testing` § 6) before saying "done"".
  - § Session End: "at most **one** kit proposal (a gap, or a rule or step to simplify)".
  - § Skepticism: "prepare the concrete change, then one question" and "An authorization already given for the same
    scope is not asked again".
- Eval cases, none of which names its skill in the prompt:
  - `dev-core`: `testing-docs-only-proof`, `testing-workflow-is-not-docs`, `testing-unchanged-result-reused`,
    `testing-correction-reruns-delta`.
  - `quality-core`: `validate-implementation-stale-record-rerun`. Its fixture has a proof log that names the base
    commit, and the head changes the checked file.
  - `core`: `session-closeout-points-to-pr`, `session-handoff-without-record`, `session-closeout-no-rerun`,
    `session-closeout-simplification-proposal`.
  - Each plugin's `INDEX.md` lists them.
- `CHANGELOG.md`: a `### Changed` line. `VERSION` is unchanged until the next release.
- Not changed:
  - The § 1 domain coverage and mutation gates.
  - The existing `validate-implementation-claimed-proof-not-rerun` eval: a claim without a record is still re-run.
  - Any kit script or CI file.

## Options considered

| Option | Verdict |
|---|---|
| A. Impact rows plus recorded-evidence reuse in the skills that own testing and validation (chosen) | One source per rule; the core line points to it; review authority stays per head |
| B. Keep "re-run every proof" and let projects override it | The conflict stays, and every project has to restate the override |
| C. A cross-head evidence cache or database in the kit | New machinery to maintain; the owner's brief excludes it |
| D. A separate always-on core line for end-of-session simplification | Core `AGENTS.md` is at its 60-line limit, and the review mode already has the single-proposal step that a signal row extends |

## Proof

- `bash platforms/tools/check.sh`, `bash platforms/tools/smoke.sh`,
  `python3 platforms/ci/validations/check_kit.py --links` and
  `gitleaks git --redact --log-opts="origin/main..HEAD"`.
- `wc -l plugins/core/AGENTS.md` prints 60.
- The eval fixtures run: each `fixture.sh` builds its repository (two commits, expected branch, the stale log names the
  base commit). The eval cases themselves run with `claude plugin eval` on demand and are not part of the gates.

## History

- 2026-10-29: confirmed (owner, chat) with the Stratics process-simplification brief; the simplification signal was
  added at the owner's request in the same session. Implemented in #101.
