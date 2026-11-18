---
id: TASK-000
feat: FEAT-000
rows: [T1]
title: "[First ~8 words of the Task cell]"
status: todo
labels: []
pr: null
created: "YYYY-MM-DD"
updated: "YYYY-MM-DD"
---
<!-- Cut by sdd-tasks when docs/spec/spec.md sets sdd.tracker: none: one file per item, named in its rows' Item cell.
     status: todo when cut; the executor sets doing or blocked; done once `pr` (owner/repo#N) merges; cancelled when a
     resync removes its rows. The body carries the rows verbatim, field by field as a GitHub task issue would: no
     rewriting, no added scope. Field contract: skill sdd-tasks, references/task-issue.md. -->

# TASK-000 — [title]

## Task

[The Task cell, verbatim; it points to `Plan § <section>` instead of restating the Plan.]

## Spec

[`docs/spec/features/FEAT-000.md`; its Relations list the REQ and decision ids, never copied here.]

## Repository

[The repository or clone the code lives in.]

## Files (owned areas)

[The Files cell: one rooted path or directory glob per area, tests included; read-only paths marked `(read-only)`.]

## Proof of completion

[The Proof cell: one command per line.]

## DoD

[Proof of completion above, plus the gate commands of `<Repository>/AGENTS.md` § Commands.]

## Covers

[CA ids]

## Depends on

[`TASK-nnn`, `FEAT-nnn Tn` or none]

## Directive

Model: [small | mid | top] | Complexity: [Low | Med | High] | Wave: [n]

## Notes

[Constraints, the do-not list, the proof allowlist location.]
