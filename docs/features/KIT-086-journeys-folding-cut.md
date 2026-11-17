---
id: KIT-086
title: "Journeys and processes, decision folding and the task cut checklist live in the kit's SDD skills"
status: in-progress
confirmed: "2026-11-16 (owner, kit chat: function map of Stratics' docs/guide/ARCHITECT.md; scope amendment \"Set of processes\" on #321)"
issue: "#321"
pr: ""
---

# KIT-086 — Journeys and processes, decision folding and the task cut checklist live in the kit's SDD skills

## Problem and evidence

[FACT] Three rules lived only in Stratics' `docs/guide/ARCHITECT.md` (read from `dev-game-studio/stratics` `main` on
2026-11-16), so no other project got them and Stratics kept restating the kit:
- delta 5, the scope and cut checklist: owned areas, protected path → label, the test folders a command handler row
  must list, hotspots;
- delta 8, journeys: a stage is planned with its journey, its rules are REQs, a review reads the spec impact;
- delta 9, folding: a settled `[DECISION]` in Open questions gets ` → folded into <Scope|CA-n|REQ-F-nnn>` when the next
  spec PR reflects it, and task status is derived;
- delta 13, cut for parallelism: chain ≤ 4, `Depends on` holds code or contract edges only, longest-chain rows at most Med;
- delta 1, bundle exclusions: `changelog.d/**`, the pilot manifest and `client/resources/i18n/**` never share an item.

Owner amendment (2026-11-16, #321): journeys are written as "journeys and processes"; a step may cite `PROC-nnn` or
`PROC-nnn S<a>–S<b>`. The process artifact, its schema, the NEED `processes` field and the `check_spec.py` /
`spec_trace.py` support are KIT-090 (#331), which builds on this record.

## Change

- `sdd-tasks/references/task-cut.md` (new): the generic cut checklist (owned areas, protected paths, required test
  folders, hotspots, chains, bundles), with its values from the profile keys `sdd.task_cut.*`, `protected_paths`,
  `max_chain` and `bundle`. `sdd-tasks` § 2-4 runs it; § 4 keeps a `bundle_exclude` row in its own item.
- `sdd-tasks/references/waves-and-models.md`: the longest-chain limit reads `task_cut.longest_chain_max_complexity`;
  `Depends on` holds code and contract edges only.
- `sdd-clarify/references/journeys.md`: "Journeys and processes": the step may cite a process once KIT-090 ships;
  until then no `PROC` reference and no "as in J-nn" step without its own links; a flow is planned with its journey;
  a change is checked through `spec_trace.py impact`.
- `sdd-plan` § 5: decision folding with `decision_folding.marker`; `sdd-clarify`, `sdd-tasks` and `sdd-review` point to it.
- `sdd-check` § 1: b covers process citations, d the task cut (`rows=` argument), e decision folding.
- `sdd-constitution/references/sdd-parameters.md`: the `task_cut` and `decision_folding` rows; `sdd-process.md`: the
  journey row names processes.
- No schema, resolver or tool changes: the keys exist since KIT-087 P1.

Left in Stratics (project facts or review-loop behaviour, not kit rules): the named test classes and fixture paths
(they become `required_test_folders` values), reachability BFS on map collision, the loop's `cut --dry-run` and
`cutcheck` steps, the `cited-write` verbs and the `earlier-task` rule, `mark-done` at batch end, and the loop's lock on
`config.json` `hotspots`.

## Proof

`platforms/tools/check.sh`, `python3.12 -B platforms/tools/run_tests.py --layer unit,contract` and
`--layer integration --changed-from origin/main`. Evals: see the PR body's `Evals:` line.

## History

- 2026-11-16: confirmed (owner), amended to "journeys and processes" (owner, #321 comment).
- 2026-11-16: skill and reference text on `feat/kit-086-journeys-folding-cut`; Stratics drops the deltas in its own PR.
