---
description: One GitHub issue per FEAT, task evidence, resync and closure; local TASK-file compatibility. Load when tracking or reviewing work.
kind: detail
---

# FEAT issue and local task items

## GitHub: one FEAT, one issue

- The issue title is `[FEAT-nnn] <FEAT title>` (use the project's feature prefix). Its body points to the FEAT and mirrors the approved table verbatim under `## Tasks` for issue-based gates; never create a task issue, bundle issue, sub-issue or separate FEAT card. The issue template remains at `platforms/kits/github/ISSUE_TEMPLATE/task.md` for installation compatibility.
- Before creating, read the FEAT's `issue`, then its legacy `card`, then search the configured backlog for the exact FEAT id. Verify identity and repository; reuse the existing FEAT issue/card even if closed. Several competing FEAT issues require reconciliation, never another issue. A later approved version reuses and, if needed, reopens the same issue.
- Save the qualified reference `OWNER/REPO#N` in `issue`; every GitHub row's `Item` names that same issue. If `card` remains for compatibility, it must name that issue's number. The issue and table are not separate backlogs.
- The body names the outcome, Spec link, affected repositories, Files union, acceptance/closure proof and the copied task table. The FEAT file remains authoritative; cut/resync refreshes the mirror without independently editing row text. Keep the repository prefixes the scope gate requires in Files. Required protected-path labels are the union across its rows.
- Within the FEAT, dependencies remain `Tn`; across FEATs, `FEAT-nnn Tn` or the other FEAT's issue. Never translate a row dependency into a dependency on its own shared issue. One FEAT may span repositories; row PRs still name their own repository and Files.
- Create/update only after table approval or merge and the user's authorized cut/resync. Pass literal text through a body file. A custom `cut_command` must obey this contract; do not invoke an old per-task cutter. Verify the returned issue before linking it; after an ambiguous creation result, search before retrying.

## Row progress and resync

- The FEAT table is authoritative for individual row Status when `issue` is set. Record `doing` with the execution reference, `blocked` with its row-specific reason, and `cancelled` with its scope decision in History. Completion uses `TRACE mark-done` with the row id and merged PR only after its proof is green; record that evidence in History. A task issue's closure or a shared issue label is not task evidence.
- `TRACE sync-status` preserves these row states and derives the aggregate FEAT status from the table. It never fans the shared issue's open, blocked, cancelled or closed state out to every task. Legacy FEATs without `issue` retain the old task-issue sync until explicitly migrated.
- Resync updates the same issue and links new approved rows to it. Keep removed rows as cancelled history and retain completed evidence; no new issue per row, wave, repository, greybox/polish pass or version. The PR unit remains independently configured by `pr_unit`.
- For an existing per-task backlog, preserve issue history. Reuse the FEAT card or create the one missing FEAT issue, copy verified row states and historical links into the FEAT, then set `issue`. Do not silently close/delete old task issues or rewrite completed rows; those changes need an explicitly scoped migration.

## PRs and closure

- A row PR selects its ids in `## Task rows` before `## Proof` (for example `T1, T2`) and uses `Refs OWNER/REPO#N`, never `Closes` on the shared FEAT issue. Its scope is only the selected approved rows. The gates read their Files from the issue's mirrored table, reject missing/unknown selections and never fall back to the whole FEAT Files union.
- The full-flow FEAT issue closes only after `sdd-review` passes the applicable closure/acceptance gate, with the closure commit and delivered PRs linked. A failed proof or pending playtest leaves it open. A later approved version reuses it.
- In the FEAT-only flow without task rows, retain its existing one-issue/one-PR behavior: that PR closes the issue and `TRACE sync-status` derives delivery. Closing an issue alone never proves delivery.

## Local tracker compatibility (`tracker: none`)

- Keep `docs/spec/tasks/TASK-nnn.md` from `spec-task.md`, one row or allowed bundle per file, with the copied rows verbatim. Its frontmatter holds `feat`, `rows`, `status`, `labels`, `pr`; each row's Item holds its TASK id.
- Task, Files, Proof of completion, Covers and Directive come from the row; Spec points to the FEAT, Repository names the code clone, and DoD adds that repository's gate commands. Depends on names the prerequisite TASK ids or uncut row ids. Notes names the project's proof allowlist.
- Local TASK status stays `todo`, `doing`, `blocked`, `done` or `cancelled`. Record delivery with the merged PR; resync derives the row Status, creates files for added rows, cancels removed rows and never rewrites a done item. Bundle limits and exclusions apply only here.
