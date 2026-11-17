---
id: KIT-091
title: "The skills write and check processes: sdd-clarify writes them, sdd-check C12, C14, C26 and Q12 grade them"
status: in-progress
confirmed: "2026-11-16 (owner, kit chat: \"concordo\" with E §§ 1-5, \"Set of processes\", E § 8.1; filing \"Sim, abra\"; scope update from E § 17, \"Sim, faça\")"
issue: "#332"
pr: ""
---

# KIT-091 — The skills write and check processes: sdd-clarify writes them, sdd-check C12, C14, C26 and Q12 grade them

## Problem and evidence

[FACT] KIT-090 (#331, merged in cc70ae0) shipped the process artifact `PROC-nnn` and its trace tools, but no skill said
when to write one or how to judge one. The owner's game-profile evaluation (`KIT-GAME-PROFILE-EVALUATION-2026-11-16.md`
in the owner's workspace, "E" below) § 9.1 maps each new item to the skill that writes, checks and uses it; § 9.2 items
3 and 4 found that `sdd-specify` and `investigate` decide fix versus improvement by "a REQ, journey or decision" only,
so a bug against a process flow would become an improvement, and that `sdd-plan` read no journey or process. § 16 adds
the writing register; § 17 (G3b) adds C26 next to C12, C14 and Q12.

## Change

- `sdd-clarify/references/processes.md` (new, beside `journeys.md`): when a flow becomes a process (shared by two flows,
  copied "as in J-nn", unseen by users, or one mechanic with states), `kind: product | tech`, the States rules (entry,
  every exit, duration with its unit; a retunable duration is a REQ Values row with its `Tunable` cell), a branch row
  per decision outcome, the feedback each actor action gets, the register, and § Soundness, which C12 reads.
  `journeys.md` points at it.
- `sdd-clarify` SKILL: a Situation may become a process step; the NEED's `processes` field; REQ Values rows carry their
  `Tunable` cell; product signs product processes, the owner team tech ones; the register rule names journeys and
  product processes.
- `sdd-check`: C12 (high, functional) a process state with no exit, an unentered state, a decision point without a row
  per outcome, or a rule as prose; C14 (medium) a `Tunable` cell empty or without range and unit (functional), or a
  non-`fixed` tunable with no Plan § Data exposure line (full); C26 (medium, functional) technical text in a NEED, a
  journey, a product process or a non-tech decision, with a grep aid and judgment; checklist Q12 (functional and full)
  each actor action names its feedback and when it appears. Findings route to `sdd-clarify`, a missing exposure to
  `sdd-plan`.
- `sdd-specify` classification and the `investigate` hand-off: "a REQ, journey, process or decision".
- `sdd-plan`: reads the NEED's journeys and processes; § Design cites each process state it implements; § Data maps each
  tunable to its exposure (`plan-sections.md`, and comments in `spec-feature.md` under Design and Data).
- No tool change: C12, C14, C26 and Q12 are judgment rows. `spec_trace.py check` already fails a non-REQ `Rules` cell,
  the mechanical half of C12.
- The NEED template gains its `processes: []` line (`templates/spec-need.md`); the schema already accepted the field.
- Out of scope: a process row in `sdd-constitution/references/sdd-process.md` § Register (C26 cites
  `processes.md` § Write for it), and the skills that use and verify processes (KIT-092).

## Proof

`bash platforms/tools/check.sh`, `bash platforms/tools/check.sh --links`, `python3.12 platforms/tools/run_tests.py --layer
unit,contract` and `--layer integration --changed-from origin/main`. No code changes, so no red test. Evals: see the PR
body's `Evals:` line.

## History

- 2026-11-16: confirmed (owner, #332 and its E § 17 update).
- 2026-11-17: implemented on `feat/kit-091-process-skills`.
