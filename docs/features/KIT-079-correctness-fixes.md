---
id: KIT-079
title: "13.0.x correctness fixes from the 13.0.0 reviews"
status: done
confirmed: "2026-11-16 (coordinator session \"Revisão de regras e skills\", under the owner's overnight autonomy: \"seja autônomo com toda liberdade e finalize o que falta\")"
issue: "#295"
pr: "#296"
---

# KIT-079 — 13.0.x correctness fixes from the 13.0.0 reviews

## Problem and evidence

[FACT] The one-round reviews of #285 (KIT-075), #263 (KIT-074) and #293 (KIT-077) filed eight defects as
non-blocking. Each can give a wrong result or lose data in a consumer project. #295 lists them with `path:line`:

1. #288 item 1: `review_checks.py dod --gates` reported a rename that stays inside the test globs, but that no `red`
   glob names, as dropped assertions (`tests/test_add.py → tests/test_add2.py`: `2 assertion lines removed`).
2. #288 item 7: a gates config without `proof_allowlist` raised `KeyError` mid-report (`pr_gates.py:559`, `:702`).
3. #288 item 3: a NUL in a proof path raised `ValueError` with a traceback (`review_checks.py:725` caught only
   `OSError`).
4. #288 item 4: `review_checks.py:502` said "a folder of its path is a file there" for every `OSError`, a name too
   long for the file system included.
5. #283 item 2: `sync-project.sh:146` `merge_driver_marked` matched `agent-rules-kit` anywhere in the file, so a
   project's own driver that mentions the kit was removed (no godot profile) or replaced (godot profile).
6. #283 item 5: `pin_sources` printed `source repo-path` with a space and `sync_pinned_plugin.py:400` split on any
   whitespace into two parts, so with a space in the repository path each just module dropped out of the pin with no
   message.
7. #294 item 1: in files mode `run_tests.py:89` loaded every module through `loadTestsFromName`, which turns only an
   `ImportError` into a failed test: the `FileNotFoundError` of a module that loads a file the PR adds stopped the
   whole base run, so `red` reported only the first new module.
8. #283 item 3: `keyed_csv_merge.py`'s record split reads every `"` as a quote, so an inch mark in an unquoted field
   (`5" screen`) leaves the file unparsable and the whole file merges as text; `merge()` promised `ValueError`, while
   an even count of such marks raises `csv.Error`.

## Change

Each item has a test that fails on `cf98ead` (output in the PR's `## Red`), then the minimal fix; nothing else moves.

1. `dod` drops a moved test's assertions when the move leaves the test globs, or leaves every `red` glob
   (`--gates`): `(old in TEST and new not in TEST) or (old in red and new not in red)`.
2. `pr_gates.REQUIRED_KEYS` gains `proof_allowlist`, so `configure` refuses a config without it and `main` exits 2
   naming the key, before any API call.
3. A proof path the file system refuses with `ValueError` (a NUL) is the same finding as an `OSError`: "the file system
   cannot check this path, not run".
4. The base-placement message says "a folder of its path is a file there" only for `FileExistsError` or
   `NotADirectoryError`; any other cause is named by its `strerror` alone.
5. `merge_driver_marked` matches line 2 of the file against the vendored driver's docstring opening,
   `"""Keyed-CSV git merge driver (agent-rules-kit KIT-074)`; a file without it is the project's.
6. `pin_sources` separates source and repo path with a tab, and `read_sources` splits on the tab; a line it cannot
   read is named on stderr instead of dropped in silence.
7. Files mode discovers each module on its own (`loader.discover` with the module's name as the pattern), so any
   import error is that module's failed test, as in a whole-folder discovery, and the next module still runs.
8. The documented fallback, not a csv-module record split: rewriting the split would change which bytes each record
   keeps, more than a minimal fix. The module text and `platforms/kits/godot/README.md` say that a `"` counts as a
   quote wherever it stands and how to write an inch mark (`"5"" screen"`); the driver's message now warns that the
   whole file merges as text, not by key, and gives that hint; `merge()` names `csv.Error` beside `ValueError`.

## Proof

The new tests and the integration classes the change reaches (`run_tests.py --layer unit,contract,integration
--changed-from origin/main`), `check.sh --links` and the linters; results in the PR.

## What would prove it wrong

A consumer report of one of the eight symptoms on a kit that contains this change.

## History

- 2026-11-16: confirmed (coordinator); issue #295. Done when its PR merges. Item 8 took the documented warning,
  which the coordinator allowed for an item larger than a minimal fix.
