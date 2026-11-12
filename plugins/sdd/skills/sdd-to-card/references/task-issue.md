---
description: Task issue contract — title, template fields, mechanical fields and cross-repo close line. Load when cutting or reviewing issues.
kind: detail
---

# Task issue — field contract

Title: `[FEAT-nnn Tn] <first ~8 words of the Task cell>`. Body: the kit issue template (`platforms/kits/github/ISSUE_TEMPLATE/task.md`, installed as `.github/ISSUE_TEMPLATE/task.md`) filled verbatim from the task row — no rewriting, no added scope.

## Field map (kit section → template field)

| Kit section | Template field |
|---|---|
| Context and goal | `Task` + `Spec` |
| Technical spec (verified paths) | `Files` |
| Parallelism (wave, files, dependencies) | `Directive` wave + `Files` + `Depends on` |
| Model directive | `Directive` model |
| DoD | `Proof of completion` + `DoD` |

## Mechanical fields

- `Spec` is the FEAT path derived from the title; REQ/DEC ids are read from the FEAT's Relations, never copied into the issue.
- `DoD` is the row's proof plus the gate commands of `<Repository>/AGENTS.md` § Commands — it adds no scope.
- `Depends on` is written `FEAT-nnn Tn` or `#N`.
- `Directive` carries `Model` (tier), `Complexity` and `Wave` from the row.

## States and close

- Freshly cut issues carry `status:proposed` until the architect approves the cut, then `status:planned`. Task issues reuse the FEAT status labels with their FEAT meaning — `labels.json` is not edited; a project that wants distinct task-level labels adds them in its own labels file.
- An implementation session picks only `status:planned` issues whose `Depends on` chain is merged.
- A task issue closes through its PR's last line `Closes <owner>/<docs-repo>#N` — cross-repo when the code lives elsewhere; the backlog repository owns the issue.
