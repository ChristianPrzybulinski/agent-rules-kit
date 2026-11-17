---
id: KIT-090
title: "The process artifact PROC-nnn, which journeys cite and the spec tools check and expand"
status: in-progress
confirmed: "2026-11-16 (owner, kit chat: \"Set of processes\", E § 8.1; scope update from E § 17, \"Sim, faça\")"
issue: "#331"
pr: ""
---

# KIT-090 — The process artifact PROC-nnn, which journeys cite and the spec tools check and expand

## Problem and evidence

[FACT] The owner's game-profile evaluation (`KIT-GAME-PROFILE-EVALUATION-2026-11-16.md` in the owner's workspace,
"E" below) § 8.1: 11 of Stratics' 65 journeys copy another journey's steps in prose ("as in J-11 S1–S7"), journeys mix
end-to-end paths with single mechanics, and flows no user sees (egg steps, the world clock, a nightly job) have no
home. The owner chose "Set of processes": journeys stay, each an ordered set of steps that may cite a process. § 14
adds `kind: product | tech` (a runbook or the vulnerability routine is a tech process); § 15: one process holds N
FEATs. KIT-086 (#321) wrote the skill text with "until KIT-090" guards; this record ships the artifact and lifts them.

## Change

- `plugins/guardrails/templates/spec-process.md` (new): frontmatter `id: PROC-nnn`, `title`, `status`, `owner`,
  `kind: product | tech`; sections Trigger, Actors, Preconditions, States (state, entry, duration and unit, experience,
  exit), Steps (action → result, Rules as REQ ids, Implemented by, Proven by), Alternative paths, Postconditions,
  Out of this process, History.
- `platforms/ci/schemas/process.schema.json` (new); `need.schema.json` gains `processes` (`PROC-nnn` ids).
- `check_spec.py`: validates `docs/spec/processes/*.md` (schema, or the structural fallback without jsonschema), a
  NEED's `processes` must name existing processes, a refined NEED may be backed by `processes` alone, and `PROC` is a
  reserved decision prefix.
- `spec_trace.py`:
  - loads processes and checks their step tables with the journey rules (Rules hold REQ ids only, tasks exist, tests
    are rooted, alternatives point at a main step, a `—` waits while an open NEED lists the process in `processes`);
  - a journey main or alternative step whose action cites `PROC-nnn` or `PROC-nnn S<a>–S<b>` (en dash or hyphen)
    holds `—` in its three link cells and takes the cited steps' rules, tasks and tests: every step, or the main steps
    S<a> to S<b> in table order plus the alternatives at them. Unknown process or step, a backwards range, another
    form, two citations, own links, a citing prerequisite and a process step citing a process fail;
  - the matrix adds Processes, Rules → processes → tests and Tasks → processes; Rules → journeys and Tasks → journeys
    list a citing step under the cited steps' rules and tasks; the matrix is required once `processes/` exists;
  - `validate` (closure) reports an unfilled step of each process a NEED lists, and of each process step a listed
    journey cites; `impact` lists a process file edit and searches process steps; `lint` reads process steps.
- REQ-F template: the Values table gains `Tunable` (`fixed`, or range and unit plus exposure);
  `sdd-clarify/references/req-scope.md` says where a tuning value goes.
- The KIT-086 guards are lifted: `sdd-clarify` (SKILL and `journeys.md`), `sdd-check` § 1 b, `sdd-tasks`,
  `sdd-constitution/references/sdd-process.md`; the journey template notes a citing step.
- Out of scope: the skills that write and check processes (KIT-091: `references/processes.md`, C12, the NEED template's
  `processes` line) and the ones that use and verify them (KIT-092); `profile.schema.json`.

## Proof

`platforms/tools/check.sh`, `python3.12 -B platforms/tools/run_tests.py --layer unit,contract` and
`--layer integration --changed-from origin/main`; new `test_spec_trace_process.py` and `test_check_spec.py`
`ProcessTest` plus three NEED and decision-kind tests, red on `origin/main` first. Backward compatibility: a spec
without `processes/` gives byte-identical `spec_trace.py check` output, matrix and `check_spec.py` output (Python
3.12 and `/usr/bin/python3` 3.9) under `origin/main` and this branch, on a copy of Stratics' `docs/spec` and on
`platforms/ci/fixtures/consumer`; `test_spec_trace_process.py` pins main's matrix for the journey fixture. Evals: see
the PR body's `Evals:` line.

## History

- 2026-11-16: confirmed (owner, #331 and its E § 17 update).
- 2026-11-16: implemented on `feat/kit-090-process-artifact`.
