---
name: sdd-tasks
description: "SDD step 5 — task rows in a planned FEAT, then their cut into items. Use when a FEAT is planned or its rows change. Not for execution (skill sdd-implement)."
argument-hint: "FEAT-nnn [cut | resync]"
triggers:
  - user
disable-model-invocation: true
allowed-tools:
  - read
  - edit
  - exec
---

# SDD 5 — Tasks

Two parts: write the rows into the FEAT and land them in a spec PR, then cut them into items once that table is approved or merged. Process: `../sdd-constitution/references/sdd-process.md`. Resolve the project profile first (`../session/references/project-profile.md`) and read `spec_root` and the `sdd` parameters `task_minutes`, `max_chain`, `max_feat_tasks`, `row_check`, `tracker`, `cut_command`, `bundle`, `protected_paths`, `journeys` (`../sdd-constitution/references/sdd-parameters.md`), `task_cut` and `decision_folding`. The cut changes GitHub or repository state: run it only on user invocation and never print a token.

## 1. Gate

Write or cut only a FEAT with `status: planned` whose Plan holds its sections (`sdd-plan` § 4); a resync also runs on `in-progress`. Anything else goes back to `sdd-plan`.

## 2. Size each row

- One row is one verifiable outcome: at most 5 areas (the `spec.md` § Architecture areas, else rooted top folders) and one proof, finished by one fresh agent context within `task_minutes`. A mechanical change across the codebase (rename, retype) is one row; a spec value a row needs (version, name, limit) is copied in verbatim.
- The Task cell names the outcome and points to `Plan § <section>`; it never restates the Plan (`check_spec.py` warns above 1000 characters).
- Split a title needing “and also”. Tests travel with behavior, never in an end-of-feature test row; a business rule's first row writes the failing domain test.
- Order contract/types → domain/tests → persistence/migration → adapters/integration → client → flag/docs.
- Dependencies are explicit only: `Depends on` names each row whose merged output this row reads (`T<n>`, or `FEAT-nnn T<n>` in another FEAT), never “the previous one”, and never an edge that stands only for an order (a migration number, a shared file). The longest chain of own rows is at most `max_chain` (`check_spec.py` fails a longer chain or a cycle), and a row on it carries at most `task_cut.longest_chain_max_complexity`. More rows than `max_feat_tasks` go back to `sdd-plan` to split the NEED.

## 3. Write the table (spec PR)

```markdown
| ID | Task | Files | Proof of completion | Covers | Depends on | Status | Complexity | Model | Wave | Item |
|---|---|---|---|---|---|---|---|---|---|---|
| T1 | Define the MoveRequest contract: Plan § Contract | `protocol/move.json`, `protocol/examples/move.json` | `python3 tools/validate.py protocol` | CA-1 | — | todo | Low | small | 0 | — |
```

- Files: rooted paths or directory globs, tests included; generated neighbours (`*.uid`, `*.import`, `*.translation`) are implicit and never listed. `Status` (`todo`, `doing`, `blocked`, `done`, `cancelled`) is derived from the item, never edited by hand. `Complexity`, `Model` and `Wave`: `references/waves-and-models.md`. `Item` is `—` until the cut.
- Coverage: every acceptance criterion appears in a row's `Covers` (each CA already cites the REQs it proves); every row covers a criterion or says it is infrastructure; run `sdd-check` row C8.
- Cut checklist: every row passes `references/task-cut.md` (owned areas, protected labels, required test folders, hotspots, chains, bundle exclusions).
- Row checks: every row passes `references/row-checks.md`; run `row_check` (`null`: the kit's `ROWS check FEAT-nnn`) and fix the rows until it exits 0.
- Fold first: each settled `[DECISION]` of the FEAT's Open questions folds where it belongs with the `decision_folding.marker` (`sdd-plan` § 5).
- Commit the table with a FEAT History line in a spec PR. The architect reviews that PR; the cut waits for its approval or merge.

## 4. Cut

When `cut_command` is set, run it on the FEAT and paste its output; otherwise cut here, in wave order:
- Items: `tracker: github` cuts one GitHub issue per item in the project's backlog repository; `tracker: none` writes one `docs/spec/tasks/TASK-nnn-slug.md` per item from `../../templates/spec-task.md`, `status: todo`. Both carry the rows verbatim: `references/task-issue.md`.
- Bundle: new rows of one repository that share a Files path go into one item within `bundle` (`rows`, `points` with Low 1, Med 2, High 3, `high_rows`); the default `rows: 1` cuts one item per row. A row whose Files match a `task_cut.bundle_exclude` glob is its own item.
- Labels: a row whose Files match a `protected_paths` entry gives its item that label.
- Write each item (`#N` or `TASK-nnn`) into its rows' `Item` cell.
- Journeys (`journeys`; absent = on when `docs/spec/journeys/` exists): fill every `—` step of the journeys this FEAT's NEED lists, a step with `Rules` `—` included: `Implemented by` takes the `FEAT-nnn Tn` rows that build it, `Proven by` the test rows, never a path to a test file that does not exist yet; add any `P<n>` row with its task. A step that cites a process (`PROC-nnn` or `PROC-nnn S<a>–S<b>`) keeps `—` in its Rules, Implemented by and Proven by: write nothing new on it, since the cited process steps carry them.
- Processes (`docs/spec/processes/`): fill, the same way, every `—` step of the processes the NEED lists in `processes` and of the process steps a listed journey cites. A process holds the rows of several FEATs: add this FEAT's rows beside the ones a step already cites and never remove another FEAT's.
- Run `TRACE check`, then commit the Item, journey and process cells together; `check_spec.py` passes.

## 5. Resync

`sdd-tasks FEAT-nnn resync` aligns rows and items after a table amendment or an item change: copy each item's state into `Status`, cut items for new approved rows, update an open item whose row text changed, close as not planned (or set `cancelled`) an item whose rows left the table, and never reopen or rewrite a `done` item. It honors `cut_command` like the cut.

## 6. Verify

Read each item as a fresh session would: if it cannot start from that text alone, add the missing fact to the row (the file to start in, a real input or output sample) and resync. An executor's “done” is not evidence; the diff and the re-run proofs are.

Done when: the rows are sized, pass the cut checklist, are explicitly ordered within `max_chain`, mapped both ways to criteria and pass the row checks in a merged or approved spec PR; every row's `Item` names its cut item; journey and process cells are filled; `check_spec.py` passes.
