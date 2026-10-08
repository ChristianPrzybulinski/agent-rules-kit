---
description: "Read-only prepare agents read a task's code, tests and spec before its implementer starts and hand it a context note. Load when planning a multi-agent pipeline."
kind: detail
---

# Read ahead: prepare agents feed the implementer

Use it when implementers spend much of their time reading before the first edit and wait for a slot or a dependency
anyway. [FACT] Stratics, P1 batch (2026-10-07): the implementers spent 62 % of their time before their first edit
(66 of 106 min), 93 % of it on model turns.

## Roles

- **Prepare agent** — read-only, one area each: (a) the production code the task changes, (b) the tests and fixtures to
  extend, (c) the spec (the task, its rows, the decisions it names, the docs it cites). One to three per task by
  complexity (Low 1, Med 2, High 3).
- **Implementer** — reads the note first, re-checks every named path and symbol on its own branch before relying on
  it, then implements.
- **Lead** (orchestrator or architect) — answers the notes' open questions before the task is handed.

## The context note

Each reader writes one file for its area; the pipeline joins them under three headings, with no extra model step:

1. **What to touch** — paths, functions or classes by name, doc sections and existing tests, each with one line on why.
2. **Step plan.**
3. **Open questions.**

## Rules

- A reader never commits, pushes, runs the proof or writes outside its note; a timeout ends it (Stratics: 20 min).
- Readers take no implement slot: start them while the task waits for a slot or a dependency, or while a batch is
  held for audit.
- A reader that fails or times out never blocks the task: the implementer reads the code itself.
- Run readers on a cheap model: reading needs breadth, not the implementer's tier.
- A note is a claim about the code when it was read, never evidence; the implementer verifies it.
- The implementer asks for every independent read in one turn (`../SKILL.md` § 2).

## Measure

Record each reader's wall time and, per implement launch, how long its slot stood free while its readers still ran
(Stratics: `waited_for_prepare_s`), and compare the time to the first edit before and after.
[HYPOTHESIS] Stratics expects the critical-path time per task to fall from about 10.8 to 6–7 min; no batch has
measured it yet.

## Example

Stratics review loop, stratics-docs FEAT-053 T23 (stratics-docs#755): `dispatch.max_prepare_children`, one
`.loop/context-<area>.md` per reader joined into `.loop/context.md`, which the implement prompt reads first.
