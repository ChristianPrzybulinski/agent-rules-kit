---
id: KIT-033
title: "An advisory script reports structural duplicates of changed GDScript functions"
status: done
confirmed: "2026-11-10 (owner, ub-mode evaluation decisions D3 and D5 in the chat of the ub-mode evaluation session; implementation prompt launched 2026-11-11)"
issue: "#135"
pr: "#143"
---

# KIT-033 — An advisory script reports structural duplicates of changed GDScript functions

## Problem and evidence

The owner evaluated the ub-mode principles against the kit on 2026-11-10
(`/Users/christian/Developer/GitHub/PROPOSAL-UB-MODE-2026-11-10.md` § 3, the duplication measurements at lines
153–167 and § 5 "KIT-032" at lines 246–256, which this feature implements under its real id) and decided that the kit
builds its own GDScript duplicate finder instead of running `dryer` (D3), with every quality check built for both
languages (D5); this one starts with GDScript and Java duplication is the proposal's follow-up. Facts re-checked at
kit `49b2137` and stratics-client `f98e0091`:

- [FACT] no code duplicate check exists in the kit: `git grep -n -i -E 'duplicat|dryer|jaccard' 49b2137 -- plugins
  platforms` finds only the Markdown paragraph check of `platforms/ci/validations/check_kit.py` § 12 (line 1121) and
  the duplicate-id checks of `check_spec.py`. `plugins/dev-core/skills/code-standards/SKILL.md:69` says "One decision
  (rule, threshold, mapping) lives in one place; every other site reads it from there." and nothing finds the copies
  that break it.
- [FACT] the parser needs no new dependency: `gdtoolkit.parser` ships with gdtoolkit, pinned at `gdtoolkit==4.5.0` in
  `platforms/kits/godot/requirements-gdtoolkit.txt:2`.
- [FACT] the prototype `/Users/christian/Developer/GitHub/UB-MODE-2026-11-10-evidence/gd_dupes.py`, run again
  read-only on a `git archive` copy of the client at `f98e0091`, prints "files 659 parse_failures 0 candidates 7359"
  and "pairs>=0.82 5620"; 564 of the pairs are production-production, 49 of those fall between 0.82 and 0.9, and
  5,042 are test-test. 5,117 pairs score 1.0. The counts are the report's (proposal lines 158–159 and 165–166).
- [FACT] three causes of that noise, read in the prototype:
  - strings are one placeholder (line 32 collapses `string`, `rstring`, `string_name` and `node_path`), so wrappers
    that differ only in their literals look identical (the report's `_request` × 9);
  - a function's last line is `meta.end_line` (line 111), which runs past trailing blank lines into the next
    declaration, so a 2-line function counts as 4 lines and passes `MIN_LINES`;
  - every tree node counts twice and its label is a fingerprint of its own (`return [node.data] + …` at line 40,
    counted by `count` at lines 61–64), so `MIN_NODES = 20` (line 20) admits functions of about 10 tree nodes.
- [FACT] the hand-checked finds of the report hold in the client: `_integer` in `app/network/stats_validator.gd:152`
  and `app/network/group_validator.gd:121` is the same function; five more validators (`daycare_validator.gd:85`,
  `editor_records_validator.gd:220`, `editor_validator.gd:479`, `mail_validator.gd:167`, `trade_validator.gd:270`)
  hold a copy that differs only in `maximum: float = INF`.

## Change

`platforms/tools/gd_duplicates.py` (new, Python 3.9+, gdtoolkit 4.5.0 already pinned):

- Usage `gd_duplicates.py [--base REF] [--all] [--threshold S] [FILE...]`. Without FILE or `--all` it compares the
  functions whose lines changed in `git diff -U0 <base>...HEAD` (default base `origin/main`, the same changed-line
  reading as `complexity.py`) with every function of the tracked `.gd` files outside `addons/`; with FILE every
  function of those files; with `--all` every pair in the tree.
- Normalisation: names become `@id` except the called name of a call and the method of an attribute call; numbers
  and type hints become placeholders; string literals stay as written. Every subtree is hashed (Merkle, blake2b-8),
  and a pair scores the Jaccard similarity of its two hash sets, pruned by set size.
- A function counts when it has 4 or more lines, its last line being the line of its last token, and 40 or more tree
  nodes. Pairs at 0.82 or more are printed on stdout as `score path:line function path:line function`, highest first.
- Parsing is most of the run, so the fingerprints of each file are cached by the SHA-256 of the cache version, the
  gdtoolkit version and the file text under `$XDG_CACHE_HOME/ai-kit/gd-duplicates` (default `~/.cache`); an entry
  is written whole or not at all, a corrupt one is parsed again, and one unused for 30 days is pruned.
- stderr holds the notices: "no changed .gd function to compare", "gdtoolkit not available (pip install gdtoolkit);
  duplicates not measured for N .gd file(s)", "not parsed: path: Error" for the first three files that fail, and the
  summary "N pair(s) at >= 0.82 for Q function(s) against C in F file(s); K file(s) not parsed".
- Exit 0. With `--threshold S`: 1 when a pair reaches S, 2 when gdtoolkit is missing. A bad ref exits 2.

`platforms/ci/validations/test_gd_duplicates.py` (new, 9 unittest cases) builds a throwaway repo with the global Git
config off: the client's `_integer` pair (copied from `f98e0091`) must be found, a `_request`-like pair that differs
only in its strings must not (an identical-strings control must), a function under each size minimum, an `addons/`
copy, a change in the next function, a file that does not parse, the cache and a stub that hides gdtoolkit. The seven
cases that need the parser skip without gdtoolkit, which the kit's CI does not install.

`platforms/tools/INDEX.md` and `platforms/ci/validations/INDEX.md` gain one row each.

`plugins/dev-core/skills/code-standards/SKILL.md` (74 → 75 lines), § 8 gains after the one-decision line: "- A new or
changed function that repeats existing code is merged into one owner every caller uses, or the PR names why the copy
stays; in GDScript, `python3 ~/.ai-kit/platforms/tools/gd_duplicates.py --base <base>` lists the pairs at 0.82 or
more (advisory)."

The skill description does not change, so its row in `plugins/dev-core/INDEX.md` stays identical; the new eval case
gains its line under `## evals/` there (`platforms/ci/validations/check_kit.py:974`–`991` fails on an unlisted case).
New eval case, not naming its skill: `plugins/dev-core/evals/code-standards-duplicate-one-owner` (the finder pairs a
copied `_integer` at 1.000 and the user wants to merge because the output is advisory; the answer gives it one owner
or asks the PR to name why the copy stays).

No CI or loop gate runs the script (D2, D5): `--threshold` waits for a measured false-positive rate. Java duplication
is out of scope (the proposal's follow-up, line 334).

## Measurements

Read-only on stratics-client at `f98e0091`, from its root, with the cache in a scratch directory; two loop gate runs
shared the machine (load average about 8), so the times compare with each other, not with the report's 21.9 s (the
prototype itself took 37.0 s in the same conditions).

| Run | Functions | Pairs ≥ 0.82 | Prod-prod | Prod in [0.82, 0.9) | Test-test | Pairs at 1.0 |
|---|---|---|---|---|---|---|
| prototype `gd_dupes.py` | 7,359 | 5,620 | 564 | 49 | 5,042 | 5,117 |
| `gd_duplicates.py --all` | 5,377 | 370 | 98 | 6 | 271 | 310 |

Each change on its own, measured with the tool's fingerprint and node count in a scratch harness that varies one
setting at a time (same 659 files):

| Strings | Last line | Min nodes | Functions | Pairs | Prod-prod | Prod in [0.82, 0.9) | Test-test |
|---|---|---|---|---|---|---|---|
| one placeholder | `meta.end_line` | 20 | 6,855 | 1,967 | 308 | 26 | 1,653 |
| kept | `meta.end_line` | 20 | 6,899 | 1,574 | 254 | 15 | 1,317 |
| one placeholder | last token | 20 | 5,893 | 608 | 156 | 17 | 449 |
| kept | last token | 20 | 5,893 | 508 | 137 | 6 | 369 |
| kept | last token | 30 | 5,759 | 451 | 124 | 6 | 325 |
| kept | last token | 40 | 5,377 | 370 | 98 | 6 | 271 |
| kept | last token | 50 | 4,934 | 304 | 60 | 4 | 243 |
| kept | last token | 60 | 4,541 | 274 | 42 | 4 | 231 |

- 40 is the highest minimum that keeps every hand-checked find: at 40 the pairs still name 7 `_integer`, 6 `_ink` and
  5 `_shape_issue` functions; at 50 the six `_ink` are gone.
- `_request` drops from the report's 9 functions to 2: `features/world/editor/editor_session.gd:193` and
  `features/world/editor/records/record_session.gd:124` at 1.000, whose strings are identical, so a real copy.
- The 6 production pairs between 0.82 and 0.9, read by hand: 4 are real copies (`_style` in `editor_panel.gd:301` and
  `schema_form.gd:627`; the sprite-set loaders `costume_art.gd:11`, `creature_art.gd:70` and `move_art.gd:11`;
  `features/battle/ui/team_card.gd:139 _bar_box` and `tools/ui/build_battle_theme.gd:172 _flat`) and 2 are signal
  wiring alike only in shape (`arena_controller.gd:19` / `daycare_controller.gd:16 _ready`, `quest_completion.gd:10` /
  `exit_gate_controller.gd:24 _init`). The 92 production pairs at 0.9 or more were not read by hand, so the tool's
  false-positive rate is not yet measured.
- Known miss: the `_integer` int copy against an `INF` copy scores 0.816 (34 against 35 fingerprints), just under 0.82.
- Cache: `app/network/stats_validator.gd` alone took 21.01 s cold (659 files parsed, 6.5 MB of cache) and 0.46 s warm;
  `--all` took 38.8 s cold and 14.3 s warm with the same output.

## Proof

Run from the worktree root at `2c66dce` on 2026-11-11 (the commits after it change only this document and
`docs/features/README.md`); every command exited 0:

- `bash platforms/tools/check.sh` and `CI=1 bash platforms/tools/check.sh`: "check: OK (14 plugins, 46 skills, 3 rules,
  22 templates, 23 indexes, 125 links, 25 hook cases)", then "✔ Validation passed" 15 times and no skip line.
- `bash platforms/tools/smoke.sh`: "smoke: OK (46 skills, app fallback, cleanup, symlink safety, manifests,
  sync-project, rules copy, vendored skills, multi-profile sync, no-spec repo)".
- `python3 platforms/ci/validations/check_kit.py --links`: "check: OK (14 plugins, 46 skills, 3 rules, 22 templates, 23
  indexes, 125 links, 25 hook cases)".
- `gitleaks git --redact --log-opts="origin/main..HEAD"`: "6 commits scanned.", "scanned ~86223 bytes (86.22 KB) in
  58ms", "no leaks found".
- `python3 -B -m unittest platforms/ci/validations/test_complexity.py`: "Ran 9 tests in 2.989s", "OK".
- `python3 -B -m unittest platforms/ci/validations/test_gd_duplicates.py`: "Ran 9 tests in 3.977s", "OK".
- New eval cases, unverified: each ran as `claude plugin eval plugins/<plugin> --case '<name>' --runs 1 --ablation none
  --no-publish --trust-plugin` and stopped before any model turn with "exit 1: Not logged in · Please run /login";
  `claude auth status` prints `"loggedIn": false` on this host, inside and outside the Bash sandbox. Cases:
  `plugins/dev-core`: `code-standards-duplicate-one-owner`.

## History

- 2026-11-10: confirmed (owner, ub-mode evaluation decisions D3 and D5).
- 2026-11-11: implementation prompt launched; issue #135.
- 2026-11-11: done in #143.
