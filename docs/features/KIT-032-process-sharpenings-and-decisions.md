---
id: KIT-032
title: "Process rules name the shared premise, a FEAT Decisions log, branch-only planned breaks and worktree cleanup"
status: confirmed
confirmed: "2026-11-10 (owner, ub-mode evaluation decisions D1, D6, D7 and D8 in the chat of the ub-mode evaluation session; implementation prompt launched 2026-11-11)"
issue: "#134"
pr: ""
---

# KIT-032 — Process rules name the shared premise, a FEAT Decisions log, branch-only planned breaks and worktree cleanup

## Problem and evidence

The owner evaluated the ub-mode process principles against the kit on 2026-11-10
(`/Users/christian/Developer/GitHub/PROPOSAL-UB-MODE-2026-11-10.md` § 3, rows 9, 12, 22 and 31–34) and decided to merge
the adopted ones into existing skills (D1), to log decisions and not actions (D6), to allow a planned break only inside
a branch with the undo named (D7), and to re-check after a compaction every figure the summary does not list as
verified (D8). Facts re-checked at kit `49b2137`:

- [FACT] `plugins/core/AGENTS.md:25` says when to stop, not what to write: "Same error twice → stop varying blindly;
  form a root-cause hypothesis before the 3rd attempt."
- [FACT] `plugins/core/AGENTS.md:17` keeps modified files and test commands through a compaction but says nothing
  about the figures a deliverable cites afterwards; the file holds 58 lines against a cap of 60.
- [FACT] `plugins/architect-sdd/skills/sdd-implement/SKILL.md:31` records only proof output: "Run the task's proof
  literally and summarize output in History."; no line allows or forbids a planned red intermediate state.
- [FACT] `plugins/architect-sdd/templates/spec-feature.md` has no `## Decisions` section (`git grep -i Decisions`
  prints nothing for the file).
- [FACT] `plugins/dev-core/skills/investigate/SKILL.md` § 4 (line 38) records impact and regression proof but never
  says a guard that hides the symptom is not a fix.
- [FACT] `plugins/core/skills/tokens/SKILL.md:15` limits what is read ("Read only the material needed for the
  requested outcome") but not where bulk output goes.
- [FACT] `plugins/core/skills/session/SKILL.md` never mentions worktrees; the only cleanup line in the kit is
  `plugins/quality-core/skills/validate-implementation/SKILL.md:33`, which removes its own `mktemp` worktree.
- [FACT] `plugins/infra-github/skills/branching-and-versioning/SKILL.md` § 3 sets the commit title format but not
  what the squash body holds.
- [FACT] the report's D8 evidence (lines 228–233): after a compaction in the evaluation session, one count came back
  as 1,785 instead of 45 lines in 7 files because `grep -h` drops file names, and a first draft of that evidence named
  five figures that no record supports; the re-check removed them.
- [FACT] a `## Decisions` line needs no new tool behaviour: `spec_trace.py` `feat_changes`
  (`platforms/ci/validations/spec_trace.py:492`–`507`) already reports any FEAT body line outside the task rows as
  "text outside the task table", History included, and template validation (`check_kit.py` `SPEC_MAP`, line 881)
  checks frontmatter only.

## Change

`plugins/core/AGENTS.md` (58 → 58 lines; two lines replaced, none added):

- Line 17: "- When compacting or summarizing context, preserve the list of modified files and the test commands
  verbatim, so the next turn can re-run the proof; after a compaction, every number, path and line a deliverable cites
  that the summary does not list as verified is re-checked before the deliverable is sent."
- Line 25: "- Same error twice → stop varying blindly; before the 3rd attempt write the premise both fixes share in one
  sentence and test or remove it. Report the worst fact first: a literal failure in sentence one."

`plugins/architect-sdd/skills/sdd-implement/SKILL.md` (48 → 50 lines):

- Step 4 appends: "When the task closes, write one line in the FEAT's `## Decisions` for each choice the spec did not
  fix: `YYYY-MM-DD T<n> (<PR>): chose X over Y because Z`; decisions only, the action log stays in the PR body."
- New paragraph after the blocker paragraph: "A planned red intermediate state (expand/contract, a failing test
  committed before its fix) is allowed only inside the task branch, with the commit body naming the undo; `main`
  never receives it."

`plugins/architect-sdd/templates/spec-feature.md` (69 → 72 lines) gains, between Tasks and Audit:
"## Decisions" with the comment "one line per choice the spec did not fix, written when its task closes:
YYYY-MM-DD T<n> (<PR>): chose X over Y because Z. New [DECISION] lines of this spec go here; Open questions keeps
only open questions. The action log stays in the PR body."

`plugins/dev-core/skills/investigate/SKILL.md` (48 → 49 lines), § 4 gains: "- A guard that only hides the symptom
(null check, catch-all, retry, default value) is not a fix unless the cause is named and the guard is the intended
behavior."

`plugins/core/skills/tokens/SKILL.md` (50 → 50 lines), § 1 gains in the same paragraph: "Bulk output (long logs, wide
searches, full test runs) goes to a subagent or a file; the main thread keeps the summary and the path."

`plugins/core/skills/session/SKILL.md` (51 → 52 lines), review mode gains: "- List the worktrees this session created
(`git worktree list`): remove only those whose branch is merged and whose tree is clean; report each one with
uncommitted work and its dirty paths, and never remove it."

`plugins/infra-github/skills/branching-and-versioning/SKILL.md` (40 → 40 lines), § 3 appends: "The squash commit body
states why, what changed and the proof (the command and its result)."

Skill descriptions do not change, so the plugin `INDEX.md` files stay identical. New eval cases, none naming its skill
except the user-only `sdd-implement`, whose prompts invoke the slash command and whose skill-fired grader is a trace
regex on its heading (precedent: `plugins/architect-sdd/evals/sdd-tasks-proof-is-executable`):

- `plugins/architect-sdd/evals/sdd-implement-decision-line` (an unfixed storage choice becomes one Decisions line)
- `plugins/architect-sdd/evals/sdd-implement-planned-red-in-branch` (a red expand step stays off `main`)
- `plugins/architect-sdd/evals/sdd-implement-actions-not-decisions` (a command list stays out of Decisions)
- `plugins/core/evals/tokens-bulk-log-summary` (fixture: a 12,000-line log with two failures; summary plus path)
- `plugins/core/evals/tokens-technical-register` (a syntax error: fix first, error text exact)
- `plugins/core/evals/tokens-human-register-no-cliches` (an outage e-mail with only the given facts)
- `plugins/infra-github/evals/branching-squash-body` (the squash body holds why, what and proof)
- `plugins/infra-github/evals/branching-no-develop-branch` (a `develop` branch request)
- `plugins/infra-github/evals/branching-incomplete-behind-flag` (half-done behavior behind a flag that defaults off)
- `plugins/core/evals/session-worktree-cleanup` (fixture: merged clean, merged dirty and unmerged worktrees)
- `plugins/dev-core/evals/investigate-guard-hides-symptom` (a null guard on a crash line)

`sdd-implement`, `tokens` and `branching-and-versioning` had no eval case before this change; each now has three.
`plugins/core/AGENTS.md` has no eval route: it is always loaded, and a case could only grade the base model with it.

## Proof

Run from the worktree root at the PR head:

<!-- proof lines are filled after the gates run -->

## History

- 2026-11-10: confirmed (owner, ub-mode evaluation decisions D1, D6, D7 and D8).
- 2026-11-11: implementation prompt launched; issue #134.
