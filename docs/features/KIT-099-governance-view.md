---
id: KIT-099
title: "A generated governance view, the C25 debt payment check and the vulnerability tech process"
status: done
confirmed: "2026-11-16 (owner, kit chat: \"Sim, faça\" on E § 17, backlog G13)"
issue: "#341"
pr: "#361"
---

# KIT-099 — A generated governance view, the C25 debt payment check and the vulnerability tech process

## Problem and evidence

[FACT] The owner's game-profile evaluation (`KIT-GAME-PROFILE-EVALUATION-2026-11-16.md` in the owner's workspace, "E"
below) § 14.1: governance is spread over profile keys (`owner_approvals`, `protected_paths`, `review`, `gates`), each
decision's `deciders` and prose, and no single view says who approves what; writing it by hand would add another copy
of `protected_paths`. A DEBT's payment `trigger` is free text that nothing reads (Stratics keeps 2 DEBT files for 131
FEATs). Security runs only at a PR or a release (skill `security`, `scan.md`), so a dependency that turns vulnerable
while no PR is open goes unseen. § 14.2 picks: no new artifact kinds; a generated `spec_trace.py governance` view, a
`spec.md § Governance` pointer, C25 for debt payment, and "keep without vulnerabilities" as a `kind: tech` process
scheduled by the owner or the loop, never a CI cron (owner policy: GitHub Actions on demand only).

## Change

- `platforms/ci/validations/spec_trace.py` (new functions, call sites `add_governance_parser(sub)` and one `governance`
  branch in `main`): `governance SPEC [--feat FEAT-nnn]` prints, read-only, Approvals (`sdd.owner_approvals`,
  `visual_approval`, `commits_by`, and `review.rounds`, `independent_reviewer`, `bar_paths.full` from the profile),
  Protected paths (`sdd.protected_paths` and `gates.protected_paths`), Decisions by kind (deciders' roles, without
  their parenthesised notes, and counts by status), Owners (ENBs and processes), Tech processes (the first Trigger line
  and the latest `- YYYY-MM-DD: run` History line as Last run, else `never`), Debts (severity, trigger, enablers and
  the payment state: `open; FEAT-nnn plans it`, `paid by FEAT-nnn`, `accepted by DEC-nnn` or `accepted; no approved
  decision names it`) and Debt payment (C25). C25 lists, for each open FEAT (or `--feat`), every open DEBT on an ENB
  the FEAT's `enablers` names that no row of the FEAT's Tasks table cites and no approved decision the FEAT cites names; it is
  off without `enablers/`. The command exits 0 whatever C25 lists (sdd-check judges each trigger) and 1 on an unknown
  `--feat` or a refused profile. Without `profile.py` beside it (a synced copy) it shows the `sdd` keys alone.
- `plugins/guardrails/templates/spec-index-business.md` and `spec-index-game.md`: a `## Governance` section after
  Architecture, a pointer to the command, worded differently in each so `check_kit.py` § 12 finds no duplicate.
- `plugins/guardrails/skills/sdd-check/SKILL.md`: row C25 (high), in the full scope with `docs/spec/enablers/`, the
  `governance=` argument (an output that exited 1 is `debt check not run`), and routing to `sdd-plan` or `sdd-tasks`
  (a row that pays the debt, or a DEC that accepts it); `sdd-plan` § 6 runs C25 beside C18 and C19.
- `plugins/guardrails/templates/spec-process.md`: a History comment, one `- YYYY-MM-DD: run: <result>` line per run of
  a `kind: tech` process, which the view shows as Last run.
- `plugins/guardrails/skills/security/references/vulnerability-process.md` (new, linked from `SKILL.md`): the example
  `PROC-nnn` (`kind: tech`) in the `spec-process.md` shape: weekly or on an advisory, run by the owner or the loop,
  steps scan `deps` and file a `fix` NEED per CVE at 7 or above, alternatives for a false positive (suppression with a
  90-day review) and an unfixable CVE (DEBT or DEC), one run line per run in History.

## Proof

`platforms/tools/check.sh`, `check.sh --links`, `python3.12 platforms/tools/run_tests.py --layer unit,contract` and
`--layer integration --changed-from origin/main`; new `test_spec_trace_governance.py` (22 tests), red before the code
(every test failed on `invalid choice: 'governance'`), green under Python 3.12 and `/usr/bin/python3` 3.9. Backward
compatibility: on `platforms/ci/fixtures/consumer` and a copy of Stratics' `docs/spec`, `spec_trace.py check`,
`generate` and `enablers` print the same output under `origin/main` and this branch (3.12 and 3.9), and the rendered
matrix has the same sha-256. The reference's example, with its placeholders filled, passes `spec_trace.py check`.

## History

- 2026-11-16: confirmed (owner, #341 from E § 17).
- 2026-11-17: implemented on `feat/kit-099-governance-view`; PR pending.
- 2026-11-17: review fixes: a debt is paid only by a Tasks row, a refused `review` or `gates` key names its
  section, `sdd-plan` runs C25, `spec-process.md` notes the run line.
- 2026-11-22: status done (#341 closed by #361; #439).
