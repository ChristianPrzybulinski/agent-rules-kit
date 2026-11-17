---
id: KIT-092
title: "The SDD skills that use and verify processes: task cells, closure and release smoke"
status: in-progress
confirmed: "2026-11-16 (owner, kit chat: \"concordo com os demais pontos das suas recomendações\", E § 8.2-8.4; filing \"Sim, abra\"; scope update from E § 17, \"Sim, faça\")"
issue: "#333"
pr: ""
---

# KIT-092 — The SDD skills that use and verify processes: task cells, closure and release smoke

## Problem and evidence

[FACT] KIT-090 (#331, merged in `cc70ae0`) ships the process artifact `PROC-nnn` and its trace tools, but the skills
that consume it still speak of journeys only: `sdd-tasks` § 4 fills the `—` cells of the journeys a NEED lists and
says nothing of the processes it lists; `sdd-review` § 1 gates on journey steps, although `spec_trace.py validate
--check` already reports an unfilled step of a listed process and of a process step a listed journey cites
(`closure_gaps`, `test_spec_trace_process.py` `ClosureTest`); `sdd-release` § 3 smokes "the main steps of every
journey the group touches", so a citing step's process steps and a server-only process no journey cites (egg steps,
the world clock, E § 9.2) are never smoked. `spec_trace.py checklist` rendered a citing step as one row whose action
is the citation, with no row for the process steps it stands for.

## Change

- `plugins/guardrails/skills/sdd-tasks/SKILL.md` § 4: journey cells as before, a citing step keeps its three `—`
  cells; new Processes bullet: fill every `—` step of the processes the NEED lists in `processes` and of the process
  steps a listed journey cites, adding this FEAT's rows beside other FEATs' rows; Done when names process cells.
- `plugins/guardrails/skills/sdd-review/SKILL.md` § 1: the gate names the process steps the tool already reports; § 3:
  a trace gap and a `manual:` check may sit on a process step.
- `plugins/guardrails/skills/sdd-release/SKILL.md` § 3: the smoke walks the expanded journey steps
  (`spec_trace.py checklist`); a touched process whose `Cited by` is `—` is smoked by its Trigger and Postconditions.
- `platforms/ci/validations/spec_trace.py` `checklist`: new `checklist_rows` follows a citing step with one
  `S<n> › PROC-nnn S<m>` row per cited step (At: the citing step's, or `PROC-nnn S<k>` for a process alternative),
  each with its rules, automated proof and manual check; new `cited_process_errors` fails the checklist before
  writing on an error of a cited process. A journey without a citing step renders byte for byte as before.
- No skill forks by `project.kind`; no closure check needed new tool support beyond KIT-090.

## Proof

`bash platforms/tools/check.sh`, `bash platforms/tools/check.sh --links`, `python3.12 platforms/tools/run_tests.py
--layer unit,contract` and `--layer integration --changed-from origin/main`; new `ChecklistTest` in
`test_spec_trace_process.py` (expansion, a whole process, a cited process's error, an unknown cited process), red
before the change (no expansion rows; a `KeyError` on a cited process's unknown REQ). `test_spec_trace_checklist.py`
stays green unchanged.

## History

- 2026-11-16: confirmed (owner, #333 and its E § 17 update).
- 2026-11-17: implemented on `feat/kit-092-process-verify-skills`.
