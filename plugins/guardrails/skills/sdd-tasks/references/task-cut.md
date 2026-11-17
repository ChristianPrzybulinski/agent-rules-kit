---
description: Task cut checklist — owned areas, protected labels, required test folders, hotspots, chains, bundle exclusions. Load when writing or cutting rows.
kind: detail
---

# Task cut checklist

What makes a task out of a FEAT row: the area it owns, the labels it needs and how it chains. The values come from the project profile (`PROFILE resolve --section sdd`, `../../session/references/project-profile.md`): `task_cut` (`owned_area_form`, `required_test_folders`, `longest_chain_max_complexity`, `bundle_exclude`), `protected_paths`, `max_chain` and `bundle`. A project never restates a rule here in its own guide; it sets a value. The writer runs the checklist on every row before the spec PR, beside `row-checks.md`, and again on the items at the cut; a row that fails is fixed in the spec, never in the implementing PR.

## Owned areas

- The `Files` cell names the areas the row owns, its tests included. With `owned_area_form: globs` (the default) a directory glob (`server/trade/**`) is the recommended form and an exact path stays valid, so an item already cut is not re-cut to change form; with `paths` the cell lists exact files and folders only.
- Every path the PR changes matches an owned area, is a generated neighbour of one (implicit, never listed) or is a changelog fragment; the scope gate (`pr_gates.py`, rule owned areas) refuses any other path.
- An existing test that reads a file the row changes (it asserts a value the row moves) joins `Files`, or the row names the row that owns it.

## Protected paths

- A `Files` path that matches a `protected_paths` entry gives the item that entry's label at the cut; the scope gate refuses a change under a protected path whose issue lacks the label, even when `Files` allows it.

## Required test folders

- `required_test_folders` maps a code glob to the test folders a row touching it also lists in `Files` (a new command handler's authorization and contract test folders, for example); the row registers its case there in the same PR. A row that touches the code glob without those folders is incomplete.

## Hotspots

- A hotspot is a central list or number every feature edits: a dispatch table, a message catalog, a translation table, a migration number, a protocol version, an error-code allocation.
- A row prefers an additive registry over editing a hotspot. When it cannot, its `Files` names the hotspot exactly, and two rows on one semantic hotspot (a number or version allocated once) never share a wave (`waves-and-models.md`).
- A file a merge tool joins safely (a union or keyed merge) is no hotspot: a row names it only to own it.

## Chains

- `Depends on` names a code or contract dependency only: a row whose merged output this row reads. An edge that stands only for an order (the next migration number, a generated table, a shared file) is not written; the merge resolves it.
- A consumer row depends on the merged contract and its fixtures, never on the producer row that fills them.
- The longest chain of own rows is at most `max_chain`; `check_spec.py` fails a longer chain or a cycle.
- A row on the longest chain carries at most `longest_chain_max_complexity` (default `Med`; `High`: no limit). A row above it is split along the Plan steps it implements, so each dependent waits only for the part it reads.

## Bundles

- New rows of one repository that share a `Files` path go into one item within `bundle` (`rows`, `points`, `high_rows`).
- A row whose `Files` match a `bundle_exclude` glob is its own item; a path in that list never makes two rows share an item.
- A bundle never contracts into a dependency cycle, and an item already cut is never added to a new bundle.

## Example

| Row | Fails | Fix |
|---|---|---|
| T2 Files `server/trade/TradeHandler.java` on a project whose `required_test_folders` maps `server/**/*Handler.java` to `server/test/authz/` | Required test folders | add `server/test/authz/**` to Files |
| T5 Depends on `T4` only because T4 takes migration `V12` first | an ordering edge | drop it; the row that merges second takes the next number |
| T6 Complexity High on the longest chain, `longest_chain_max_complexity: Med` | Chains | split T6 along its Plan steps at Med or Low |
