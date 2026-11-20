---
name: sdd-tasks
description: "SDD step 5 — task rows of a FEAT and its one issue. Use when a FEAT is planned, its rows change or a fix needs one. Not for execution (skill sdd-implement)."
argument-hint: "FEAT-nnn [cut | resync | fix NEED-nnn]"
triggers:
  - user
disable-model-invocation: true
allowed-tools:
  - read
  - edit
  - exec
---

# SDD 5 — Tasks

Write the rows into the FEAT and land them in a spec PR, then create or reuse its single tracking issue once that table is approved or merged. With `tracker: github`, one FEAT always has one issue; rows, waves, bundles and version blocks never create additional issues. Process: `../sdd-constitution/references/sdd-process.md`. Resolve the project profile first (`../session/references/project-profile.md`) and read `spec_root` and the `sdd` parameters `task_minutes`, `max_chain`, `max_feat_tasks`, `row_check`, `tracker`, `cut_command`, `bundle`, `protected_paths`, `journeys` (`../sdd-constitution/references/sdd-parameters.md`), `passes`, `task_cut` and `decision_folding`. The cut changes GitHub or repository state: run it only on user invocation and never print a token. With `sdd.task_table: false` (the `tooling` preset, set with `sdd.flow: feat-only`; KIT-100) this step does not run: the FEAT is the item, one issue and one PR, and its status follows that PR (`TRACE sync-status`); say so and stop.

## 1. Gate

Write or cut only a FEAT with `status: planned` whose Plan holds its sections (`sdd-plan` § 4); a resync also runs on `in-progress`, and `fix NEED-nnn` (§ 7) takes a FEAT in any status. Anything else goes back to `sdd-plan`. Under `sdd.passes` (KIT-094), a polish block's rows are written and cut only once the FEAT's History holds its greybox block's playtest line with outcome `go` (`../sdd-review/references/playtest.md`); without it the polish waits. A greybox block's rows need no `evidence:` clause (`references/row-checks.md` rule j).

## 2. Size each row

- One row is one verifiable outcome: at most 5 areas (the `spec.md` § Architecture areas, else rooted top folders) and one proof, finished by one fresh agent context within `task_minutes`. A mechanical change across the codebase (rename, retype) is one row; a spec value a row needs (version, name, limit) is copied in verbatim.
- With `docs/spec/enablers/`, size by ENB: a row changes the code of one ENB (its Code paths) and the contracts that ENB provides or requires; work across two ENBs splits at the contract between them, the provider's row first and the consumer's `Depends on` it. A part outside every ENB (build, tooling) counts by its area row.
- The Task cell names the outcome and points to `Plan § <section>`; it never restates the Plan (`check_spec.py` warns above 1000 characters).
- A homogeneous set (the 151 species references, N move handlers, N quests or items) is never one row per item: data every item holds in one form is ONE row driven by a table or generator plus a test that iterates the set; behaviour that differs per item under one contract is one row per group of items sharing that contract and test fixture (a category), its items named in the Task cell; a row per item only when that item has its own contract, files no other item touches or an owner decision. A FEAT is cut so it can be one issue: split it only at an independent module or a real breaking dependency (`references/task-cut.md` § Homogeneous sets).
- Split a title needing “and also”. Tests travel with behavior, never in an end-of-feature test row; a business rule's first row writes the failing domain test.
- Order contract/types → domain/tests → persistence/migration → adapters/integration → client → flag/docs.
- Dependencies are explicit only: `Depends on` names each row whose merged output this row reads (`T<n>`, or `FEAT-nnn T<n>` in another FEAT), never “the previous one”, and never an edge that stands only for an order (a migration number, a shared file). The longest chain of own rows is at most `max_chain` (`check_spec.py` fails a longer chain or a cycle), and a row on it carries at most `task_cut.longest_chain_max_complexity`. More rows than `max_feat_tasks` go back to `sdd-plan` to split the NEED, or, in a FEAT with `## Versions`, to the next block (`check_spec.py` fails an open block above it).

## 3. Write the table (spec PR)

```markdown
| ID | Task | Files | Proof of completion | Covers | Depends on | Status | Complexity | Model | Wave | Item |
|---|---|---|---|---|---|---|---|---|---|---|
| T1 | Define the MoveRequest contract: Plan § Contract | `protocol/move.json`, `protocol/examples/move.json` | `python3 tools/validate.py protocol` | CA-1 | — | todo | Low | small | 0 | — |
```

- In a FEAT with `## Versions` the table goes in the open block's `#### Tasks`; row ids continue across blocks and are never reused. Once the block's rows are planned, a row is added only for a defect or a missing step of a REQ in the block's Scope, with a History line naming the row and the defect or REQ (`sdd-check` C17); other new work goes to the next block.
- Files: rooted paths or directory globs, tests included; generated neighbours (`*.uid`, `*.import`, `*.translation`) are implicit and never listed. `Status` (`todo`, `doing`, `blocked`, `done`, `cancelled`) belongs to each row: with a canonical FEAT `issue`, record row-specific execution evidence in History and use `TRACE mark-done` with the merged PR for completion. The shared issue never supplies a row status. Legacy task issues and `tracker: none` TASK files retain their derived status. `Complexity`, `Model` and `Wave`: `references/waves-and-models.md`. `Item` is `—` until the cut.
- Walk table (with `docs/spec/enablers/`): write into each row of Plan § Design's walk table the row ids that build its ENB contract; a walk row with no task row is a gap to fix here.
- Coverage: every acceptance criterion appears in a row's `Covers` (each CA already cites the REQs it proves); every row covers a criterion or says it is infrastructure; run `sdd-check` row C8.
- Cut checklist: every row passes `references/task-cut.md` (owned areas, protected labels, required test folders, hotspots, chains, bundle exclusions).
- Row checks: every row passes `references/row-checks.md`; run `row_check` (`null`: the kit's `ROWS check FEAT-nnn`) and fix the rows until it exits 0.
- Fold first: each settled `[DECISION]` of the FEAT's Open questions folds where it belongs with the `decision_folding.marker` (`sdd-plan` § 5).
- Commit the table with a FEAT History line in a spec PR. The architect reviews that PR; the cut waits for its approval or merge.

## 4. Cut

For GitHub, first verify that any `cut_command` creates or updates one issue for the whole FEAT. Never run a command that emits row or bundle issues: report the exact incompatible command and use the procedure below, or adapt it in a separately scoped project change. A compatible command is idempotent and returns the existing issue on resync. With `tracker: none`, keep the configured cut or the local TASK procedure below:
- GitHub: create or reuse the single FEAT issue as `references/task-issue.md` specifies. Save its qualified reference in FEAT frontmatter `issue` and put that same reference in every row's `Item`. Reuse an existing FEAT card; never create both a card and an issue. The table remains the source of task scope, dependencies and proofs.
- Local tracker only: `tracker: none` writes one `docs/spec/tasks/TASK-nnn.md` per row or bundle from `../../templates/spec-task.md`, with `status: todo` and the rows verbatim. Its `bundle` limits and `task_cut.bundle_exclude` still apply. These settings never split GitHub issues.
- Labels: the FEAT issue gets the union of labels required by all rows' `protected_paths`; local TASK items get their own rows' labels.
- Verify the returned issue reference before writing Item cells; on an ambiguous creation failure, search for the FEAT before retrying. Local TASK ids go into their rows' Item cells.
- Journeys (`journeys`; absent = on when `docs/spec/journeys/` exists): fill every `—` step of the journeys this FEAT's NEED lists, a step with `Rules` `—` included: `Implemented by` takes the `FEAT-nnn Tn` rows that build it, `Proven by` the test rows, never a path to a test file that does not exist yet; add any `P<n>` row with its task. A step that cites a process (`PROC-nnn` or `PROC-nnn S<a>–S<b>`) keeps `—` in its Rules, Implemented by and Proven by: write nothing new on it, since the cited process steps carry them.
- Processes (`docs/spec/processes/`): fill, the same way, every `—` step of the processes the NEED lists in `processes` and of the process steps a listed journey cites. A process holds the rows of several FEATs: add this FEAT's rows beside the ones a step already cites and never remove another FEAT's.
- Run `TRACE check`, then commit the Item, journey and process cells together; `check_spec.py` passes.

## 5. Resync

`sdd-tasks FEAT-nnn resync` updates the same GitHub issue and maps new approved rows to it, preserving row-specific Status and evidence. Retain removed rows as cancelled history; never close the FEAT issue because one row left. A later approved version reopens the same issue when needed, never creates a new one. Existing per-task issues are historical: do not bulk-close or delete them; migrate their verified row states and references explicitly before setting the canonical `issue`. With `tracker: none`, keep deriving row status from TASK files, create files for new rows, cancel removed rows and never rewrite a done item. Honor only a compatible `cut_command`.

## 6. Verify

Read the FEAT and its linked issue (or TASK file) as a fresh session would: if it cannot start from those artifacts, add the missing fact to the row (the file to start in, a real input or output sample) and resync. An executor's “done” is not evidence; the diff and the re-run proofs are.

## 7. Fix (`sdd-tasks FEAT-nnn fix NEED-nnn`)

For a `fix` NEED that `sdd-specify` routed and whose code change has no row. The FEAT is the one `sdd-specify` § 1 names (the owner of the cited artifact's behavior, or the one whose rows' Files hold the code); never a new FEAT. §§ 2 and 3 size and check the one row.

- Gate: the NEED is `routed` (or `triaged` with its fix route confirmed); the FEAT may have any status, `planned` is not required.
- Write one row and one CA, the NEED in the origin of both: the Task cell names the outcome, the violated artifact's path (or, for a defect no artifact states, the evidence) and `NEED-nnn`; the CA's Given names the same NEED, and its `Proves` is the REQ the fix restores (`—` for a defect no artifact states, `sdd-plan` § 1); the row `Covers` it. In a FEAT with `## Versions` they go in the open block.
- A delivered FEAT takes them in its next version block (`sdd-plan` § 1 opens it) as an exception: its History line names the NEED, the row and why, and its frontmatter `status` takes the new block's status by hand (`check_spec.py` fails a FEAT whose status differs from its last block's, and `sync-status` leaves a FEAT at `delivered`, `validated` or `cancelled` as it is, `STATUS_FROZEN`; only a `validated` one with an open row moves, to `in-progress`). A `validated` FEAT first goes back to `in-progress` (`sdd-intake` § 4), since § 1 lets `resync` run only on `planned` or `in-progress`.
- Run the row check (§ 3) until it exits 0, add the FEAT History line, and name the row in the NEED's `routed` History line. Then the spec PR lands and § 5 maps the row.

Done when: the rows are sized, pass the cut checklist, are explicitly ordered within `max_chain`, mapped both ways to criteria and pass the row checks in a merged or approved spec PR; every GitHub row's `Item` names the FEAT's one issue (or its local TASK item); journey and process cells are filled; `check_spec.py` passes. A fix: the one row and its CA pass the row checks and the NEED names the row (§ 7).
