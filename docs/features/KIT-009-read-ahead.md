---
id: KIT-009
title: "Read ahead: read-only prepare agents feed the implementer in multi-agent pipelines"
status: done
confirmed: "2026-10-08 (owner, chat of the Stratics P1/P2 orchestrator session: \"7 aprovo\")"
issue: "#83"
pr: "#86"
---

# KIT-009 — Read ahead: read-only prepare agents feed the implementer in multi-agent pipelines

## Problem and evidence

[FACT] The kit's `parallelize` skill fans out disjoint tasks but says nothing about the time an implementer spends
reading before it can edit. In the Stratics P1 batch (2026-10-07) the implementer agents spent 62 % of their time
before their first edit, 66 of 106 min, and 93 % of it on model turns (stratics-docs FEAT-053 T23).

[FACT] Stratics answered with a prepare stage (FEAT-053 T23, stratics-docs#755): while a task waits for a slot or a
dependency, or while a batch is held for audit, one to three read-only prepare agents per task (by complexity) each
read one area — the code to change, the tests to extend, the spec — on a free model and write a note; the notes are
joined into one context file that the implementer reads first and re-checks; the readers' open questions reach the
architect's audit before the hand-off; a reader never commits and has a 20 min timeout.

[HYPOTHESIS] The gain is unmeasured: the Stratics proposal expects the critical-path time per task to fall from about
10.8 to 6–7 min, to be checked with the loop's `waited_for_prepare_s` and the time to first edit.

## Change

- `plugins/core/skills/parallelize/SKILL.md` § 4 gains: "While a task waits for a slot or a dependency, read ahead:
  read-only prepare workers, one per area (code, tests, spec), write a context note that the implementer reads first
  and re-checks (`references/read-ahead.md`)."
- New `plugins/core/skills/parallelize/references/read-ahead.md`: when it pays, the three roles, the note's three
  headings, the rules (read-only, timeout, no implement slot, never blocking, cheap model, a note is not evidence), how
  to measure it, and the Stratics implementation as the example.

## Proof

`bash platforms/tools/check.sh`; `bash platforms/tools/smoke.sh`; `python3 platforms/ci/validations/check_kit.py --links`.

## History

- 2026-10-08: confirmed (owner, chat of the Stratics P1/P2 orchestrator session) and done.
